#!/usr/bin/env python

import sys
import signal

from decouple import config

from server import Server, CustomHTTPServer
from visualization import Visualization


PORT = config('HTTP_PORT', default=8080, cast=int)

# LED strip configuration:
LED_COUNT = config('LED_COUNT', default=300, cast=int)  # Number of LED pixels.
LED_PIN = config('LED_PIN', default=18, cast=int)  # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = config('LED_FREQ_HZ', default=800000, cast=int)  # LED signal frequency in hertz (usually 800khz)
LED_DMA = config('LED_DMA', default=5, cast=int)  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = config('LED_BRIGHTNESS', default=255, cast=int)  # Set to 0 for darkest and 255 for brightest
# True to invert the signal (when using NPN transistor level shift)
LED_INVERT = config('LED_INVERT', default=False, cast=bool)


def shutdown():
    print('shutdown starting')
    visualization.close()
    sys.exit()


def signal_handler(signal, frame):
    print('You pressed Ctrl+C')
    shutdown()


signal.signal(signal.SIGINT, signal_handler)
visualization = Visualization(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_BRIGHTNESS, LED_INVERT)
httpd = CustomHTTPServer(("", PORT), Server)
visualization.loop(shutdown, httpd)
