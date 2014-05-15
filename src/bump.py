#!/usr/bin/env python

### Class to control the two front bump sensors ###

import Adafruit_BBIO.GPIO as GPIO
import time

class BumpSensor(object):
    def __init__(self, black_pin = "P8_7", tan_pin = "P8_26"):

        self.black_pin = black_pin
        self.tan_pin = tan_pin

        GPIO.setup(self.black_pin, GPIO.IN)
        GPIO.setup(self.tan_pin, GPIO.IN)

    def didBump(self):
        old_switch_state = 0
        while True:
            time.sleep(0.5)
            new_switch_state = GPIO.input(self.black_pin) and GPIO.input(self.tan_pin)
            print new_switch_state
            if new_switch_state == 0:
                print 'We have bumped!'
                return 1
            else:
                pass
