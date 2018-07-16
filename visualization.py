import math
import time
import numpy

try:
    from neopixel import PixelStrip
    has_pixels = True
except Exception:
    has_pixels = False
    import pygame

from recorder import SwhRecorder


class PyGamePixels(object):

    def __init__(self, screen, boxes):
        self.screen = screen
        self.boxes = boxes

    def setPixelColorRGB(self, idx, r, g, b):
        self.screen.fill((r, g, b), self.boxes[idx])

    def show(self):
        pygame.display.update()


class Visualization(object):

    VISUALIZATION_METHOD_CHOICES = (
        ('frequency_color', 'Frequency Color'),
        ('single_frequency_amplitude', 'Single Frequency Color'),
        ('color_change_frequency_amplitude', 'Color Change Frequency Amplitude'),
        ('frequency_color_frequency_amplitude', 'Frequency Color Frequency Amplitude'),
        ('frequency_color_shift_frequency_amplitude', 'Frequency Color Shift Frequency Amplitude'),
    )
    VISUALIZATION_METHODS = [choice[0] for choice in VISUALIZATION_METHOD_CHOICES]
    visualization_method = VISUALIZATION_METHODS[-1]
    single_frequency_amplitue_color = (255, 255, 255)
    max_db = 20000
    max_db_length = 25  # number of samples to use for weighted average of max db
    max_db_array = []
    max_db_weights = []

    def __init__(self, led_count, led_pin, led_freq_hz, led_dma, led_brightness, led_invert):
        self.led_count = led_count
        self.led_pin = led_pin
        self.led_freq_hz = led_freq_hz
        self.led_dma = led_dma
        self.led_brightness = led_brightness
        self.led_invert = led_invert

        for i in range(self.max_db_length):
            self.max_db_array.append(self.max_db)
            if i / (self.max_db_length / 3) < 1:
                self.max_db_weights.append(.5)
            elif i / (self.max_db_length / 3) < 2:
                self.max_db_weights.append(.8)
            else:
                self.max_db_weights.append(1)

        self.dbs = []
        for _ in range(self.led_count):
            self.dbs.append(0)

        self.start_time = time.time()
        self.iterations = 0

        self.SR = SwhRecorder(buckets=self.led_count)
        self.SR.setup()
        self.SR.continuousStart()

        if has_pixels:
            # Create NeoPixel object with appropriate configuration.
            self.strip = PixelStrip(
                self.led_count, self.led_pin, self.led_freq_hz, self.led_dma, self.led_invert, self.led_brightness)
            # Intialize the library (must be called once before other functions).
            self.strip.begin()
        else:
            pygame.init()
            size = 20
            width = int(math.sqrt(self.led_count))
            self.screen = pygame.display.set_mode((size * width, size * (width + 1)))
            self.boxes = []
            for led in range(self.led_count):
                y = int(led / width) * size
                x = led % width * size
                box = pygame.Rect(x, y, size, size)
                color = int((led * 255.) / self.led_count)
                self.screen.fill((color, color, color), box)
                self.boxes.append(box)
            pygame.display.update()
            # patch neopixel functions onto pygame so we don't need if statements
            self.strip = PyGamePixels(self.screen, self.boxes)

    def close(self):
        self.SR.close()
        if has_pixels:
            pygame.quit()

    def run_fft(self):
        ys = self.SR.fft()
        if ys is None:
            return False

        for led in range(self.led_count):
            led_num = int(led * (len(ys) / self.led_count))
            db = ys[led_num]
            if db > self.dbs[led]:  # jump up fast
                self.dbs[led] = db
            else:  # fade slowly
                self.dbs[led] = int((self.dbs[led] * 2 + db * 3) / 5)

        self.max_db_array.pop(0)
        self.max_db_array.append(max(self.dbs))
        # use weighted avg for max then set top 95% as max
        self.max_db = numpy.average(self.max_db_array, weights=self.max_db_weights) * .95
        return True

    def set_visualization_method(self, method):
        self.visualization_method = method

    def loop(self, shutdown, httpd):
        while True:
            if self.run_fft():
                self.display_fft()
                httpd.serve_once(self.set_visualization_method)
                if not has_pixels:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            shutdown()
                self.iterations += 1
                if self.iterations % 100 == 0:
                    print('Frame Rate: {}'.format(self.iterations / (time.time() - self.start_time)))

    def write_pixel(self, index, rgb_color):
        self.strip.setPixelColorRGB(index, *rgb_color)

    # Heavily optimized for s=1 and v=1
    def hsv_to_rgb(self, h):
        i = int(h*6.)  # XXX assume int() truncates!
        f = (h*6.)-i; q,t = int(255*(1.-f)), int(255*f); i%=6
        if i == 0: return (255, t, 0)
        if i == 1: return (q, 255, 0)
        if i == 2: return (0, 255, t)
        if i == 3: return (0, q, 255)
        if i == 4: return (t, 0, 255)
        if i == 5: return (255, 0, q)

    def display_frequency_color(self):
        for led in range(self.led_count):
            # blue is low and red is high
            self.write_pixel(led, self.hsv_to_rgb((.7 - (self.dbs[led] / self.max_db)) % 1))

    def display_single_frequency_amplitude(self):
        for led in range(self.led_count):
            multiplier = min(self.dbs[led] / self.max_db, 1)
            rgb_color = [int(color * multiplier) for color in self.single_frequency_amplitue_color]
            self.write_pixel(led, rgb_color)

    def display_color_change_frequency_amplitude(self):
        time_fraction = ((time.time() - self.start_time) / 8) % 1  # rotate from 0 to 1 in 8 seconds
        colors = self.hsv_to_rgb(time_fraction, 1, 1)

        for led in range(self.led_count):
            multiplier = min(self.dbs[led] / self.max_db, 1)
            rgb_color = [int(color * multiplier) for color in colors]
            self.write_pixel(led, rgb_color)

    def display_frequency_color_frequency_amplitude(self):
        for led in range(self.led_count):
            colors = self.hsv_to_rgb(led / self.led_count)
            multiplier = min(self.dbs[led] / self.max_db, 1)
            rgb_color = [int(color * multiplier) for color in colors]
            self.write_pixel(led, rgb_color)

    def display_frequency_color_shift_frequency_amplitude(self):
        time_fraction = ((self.start_time - time.time()) / 8) % 1  # rotate from 0 to 1 in 8 seconds

        for led in range(self.led_count):
            colors = self.hsv_to_rgb(((led / self.led_count) + time_fraction) % 1)
            multiplier = min(self.dbs[led] / self.max_db, 1)
            rgb_color = [int(color * multiplier) for color in colors]
            self.write_pixel(led, rgb_color)

    def display_fft(self):
        getattr(self, 'display_{}'.format(self.visualization_method))()
        self.strip.show()
