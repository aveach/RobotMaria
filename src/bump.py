#!/usr/bin/env python

### Class to control the two front bump sensors ###

import Adafruit_BBIO.GPIO as GPIO
import time

class BumpSensor(object):
    def __init__(self, black_pin = "P8_20", tan_pin = "P8_22"):

        self.black_pin = black_pin
        self.tan_pin = tan_pin

        GPIO.setup(self.black_pin, GPIO.IN)
        GPIO.setup(self.tan_pin, GPIO.IN)

    def didBump():
        old_switch_state = 0
        while True:
            new_switch_state = GPIO.input(self.black_pin) or GPIO.input(self.tan_pin)
            if new_switch_state == 1 and old_switch_state == 0 :
                print 'Button Pressed!'
                time.sleep(0.1)
                old_switch_state = new_switch_state
