# NeoPixel_FFT

Neopixel visualizer for audio FFT signal.

This can be run from OSX for development purposes using the pygame library to emulate pixels.

You will need a USB microphone or a USB headphone jack to process audio on the Raspberry Pi. The code uses PWM and a DMA to accurately write to the NeoPixels. You should use a high speed level converter to shift from 3.3V to 5V data. The default pin used is GPIO 18.

The algorithm takes the number of LEDs you have, and attempts to create FFT buckets from 16Hz to 5000Hz in even increments for each LED.

There are several different visual algorithms to choose between. There is a server that runs by default on port 8080 that allows you to easily change the display algorithm.

## Resin.io

Visit resin.io for information about what the service provides. Essentially, you can create an account and push a copy of this repository to your resin git project, and you will be up and running.

# Installation

## OSX

```
brew install portaudio pipenv
pipenv install
```

## RaspberryPi

```
sudo apt-get install portaudio19-dev python3-dev
pip3 install -r requirements.txt
```

# Usage

## OSX

```
pipenv run ./run.sh
```

## RaspberryPi

```
bash ./run.sh
```

# Changing Settings

Add settings to `.env` file

```
HTTP_PORT=80
LED_COUNT=150
LED_PIN=5
LED_FREQ_HZ=400000
LED_DMA=10
LED_BRIGHTNESS=150
LED_INVERT=True
```
