#!/usr/bin/env python

### Class to control the RGB LED Indicator ###

import Adafruit_BBIO.GPIO as GPIO

class RGBController(object):
    def __init__(self, red_pin = "P8_10", green_pin = "P8_12", blue_pin =  "P8_14"):

        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin

        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.output(self.red_pin, GPIO.LOW)

        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.output(self.green_pin, GPIO.LOW)

        GPIO.setup(self.blue_pin, GPIO.OUT)
        GPIO.output(self.blue_pin, GPIO.LOW)

    def turnOn(self, color):
        if color == "red":
            GPIO.output(self.red_pin, GPIO.HIGH)
        elif color == "green":
            GPIO.output(self.green_pin, GPIO.HIGH)
        elif color == "blue":
            GPIO.output(self.blue_pin, GPIO.HIGH)
        elif color == "purple":
            GPIO.output(self.red_pin, GPIO.HIGH)
            GPIO.output(self.blue_pin, GPIO.HIGH)
        else:
            pass

    def turnOff(self, color):
        if color == "red":
            GPIO.output(self.red_pin, GPIO.LOW)
        elif color == "green":
            GPIO.output(self.green_pin, GPIO.LOW)
        elif color == "blue":
            GPIO.output(self.blue_pin, GPIO.LOW)
        elif color == "purple":
            GPIO.output(self.red_pin, GPIO.LOW)
            GPIO.output(self.blue_pin, GPIO.LOW)
        else:
            pass

    def allOff(self):
        GPIO.output(self.red_pin, GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.LOW)
