#!/usr/bin/env python

import sys
import signal

from server import Server, CustomHTTPServer
from visualization import Visualization


PORT = 8080

# LED strip configuration:
LED_COUNT = 300  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)


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
