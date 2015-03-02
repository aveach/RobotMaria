#!/usr/bin/env python

import Adafruit_BBIO.GPIO as GPIO
import time

red_pin = "P8_10"
green_pin = "P8_12"
blue_pin =  "P8_14"

GPIO.setup(red_pin, GPIO.OUT)
GPIO.output(red_pin, GPIO.LOW)

GPIO.setup(green_pin, GPIO.OUT)
GPIO.output(green_pin, GPIO.LOW)

GPIO.setup(blue_pin, GPIO.OUT)
GPIO.output(blue_pin, GPIO.LOW)

while True:
        
    print "Turning on Red"
    GPIO.output(red_pin, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(red_pin, GPIO.LOW)

    print "Turning on Green"
    GPIO.output(green_pin, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(green_pin, GPIO.LOW)

    print "Turning on Blue"
    GPIO.output(blue_pin, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(blue_pin, GPIO.LOW)
