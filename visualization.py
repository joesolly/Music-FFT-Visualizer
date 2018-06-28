import math
import time
import colorsys

try:
    from neopixel import Adafruit_NeoPixel
    has_pixels = True
except Exception:
    has_pixels = False
    import pygame

from recorder import SwhRecorder


class Visualization(object):

    VISUALIZATION_METHOD_CHOICES = (
        ('frequency_color', 'Frequency Color'),
        ('single_frequency_amplitude', 'Single Frequency Color'),
        ('color_change_frequency_amplitude', 'Color Change Frequency Amplitude'),
        ('frequency_color_frequency_amplitude', 'Frequency Color Frequency Amplitude'),
    )
    VISUALIZATION_METHODS = [choice[0] for choice in VISUALIZATION_METHOD_CHOICES]
    visualization_method = VISUALIZATION_METHODS[-1]
    single_frequency_amplitue_color = (255, 255, 255)
    max_db = 1020

    def __init__(self, led_count, led_pin, led_freq_hz, led_dma, led_brightness, led_invert):
        self.led_count = led_count
        self.led_pint = led_pin
        self.led_freq_hz = led_freq_hz
        self.led_dma = led_dma
        self.led_brightness = led_brightness
        self.led_invert = led_invert

        self.dbs = []
        for _ in range(self.led_count):
            self.dbs.append(0)

        self.start_time = time.time()

        self.SR = SwhRecorder()
        self.SR.setup()
        self.SR.continuousStart()

        if has_pixels:
            # Create NeoPixel object with appropriate configuration.
            self.strip = Adafruit_NeoPixel(
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

    def close(self):
        self.SR.close()
        if has_pixels:
            pygame.quit()

    def run_fft(self):
        xs, ys = self.SR.fft(trimBy=False)

        for led in range(self.led_count):
            # 15 -> 315 is the frequency range for most music (deep bass should probably remove the +15)
            led_num = int(led * (300 / self.led_count)) + 15
            db = int(ys[led_num] / (20 - (led / (self.led_count / 20)) + 1))
            if db > self.dbs[led]:  # jump up fast
                self.dbs[led] = db
            else:  # fade slowly
                self.dbs[led] = int((self.dbs[led] * 2 + db) / 3)

    def set_visualization_method(self, method):
        self.visualization_method = method

    def loop(self, shutdown, httpd):
        while True:
            if not has_pixels:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        shutdown()
            self.run_fft()
            self.display_fft()
            httpd.serve_once(self.set_visualization_method)

    def write_pixel(self, index, rgb_color):
        if has_pixels:
            self.strip.setPixelColor(index, *rgb_color)
        else:
            self.screen.fill(rgb_color, self.boxes[index])

    def hsv_to_rgb(self, color_fraction):
        color_fraction = max(0, min(color_fraction, 1))
        return [int(color * 255) for color in colorsys.hsv_to_rgb(color_fraction, 1, 1)]

    def display_frequency_color(self):
        for led in range(self.led_count):
            self.write_pixel(led, self.hsv_to_rgb((.7 - (self.dbs[led] / 1020)) % 1))

    def display_single_frequency_amplitude(self):
        for led in range(self.led_count):
            rgb_color = [
                min(int(color * self.dbs[led] / self.max_db), 255) for color in self.single_frequency_amplitue_color]
            self.write_pixel(led, rgb_color)

    def display_color_change_frequency_amplitude(self):
        time_fraction = ((time.time() - self.start_time) / 8) % 1  # rotate from 0 to 1 in 8 seconds
        colors = colorsys.hsv_to_rgb(time_fraction, 1, 1)

        for led in range(self.led_count):
            rgb_color = [
                min(int(color * 255 * self.dbs[led] / self.max_db), 255) for color in colors]
            self.write_pixel(led, rgb_color)

    def display_frequency_color_frequency_amplitude(self):
        for led in range(self.led_count):
            colors = self.hsv_to_rgb(led / self.led_count)
            rgb_color = [
                min(int(color * self.dbs[led] / self.max_db), color) for color in colors]
            self.write_pixel(led, rgb_color)

    def display_fft(self):
        getattr(self, 'display_{}'.format(self.visualization_method))()

        if has_pixels:
            self.strip.show()
        else:
            pygame.display.update()
