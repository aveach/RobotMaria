#!/usr/bin/env python

### Class to control the two front bump sensors ###

import Adafruit_BBIO.GPIO as GPIO
import time
import sensorState

class BumpSensor(sensorState.Sensor):
  def __init__(self, inName, inDefaultPriority=3, black_pin = "P8_7", tan_pin = "P8_26", **kwargs):
    # boilerplate bookkeeping
    sensorState.Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc,
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=3)

    self.black_pin = black_pin
    self.tan_pin = tan_pin
    self.switch_state = 0
    self.didBump = 0

    GPIO.setup(self.black_pin, GPIO.IN)
    GPIO.setup(self.tan_pin, GPIO.IN)


  # service the sensor, post the value
  def __threadProc(self, **kwargs):
    while not self.quitEvent_.isSet():                      # should we quit?

        self.switch_state = GPIO.input(self.black_pin) and GPIO.input(self.tan_pin)
        if self.switch_state == 0:
            self.didBump = 1
        else:
            self.didBump = 0
        time.sleep(0.1)
        print "\Bump sensor %s SPEAKS: %s" % (self.name_, self.didBump)
        self.postReading(self.didBump, 1)                       # "high" priority
    
    while self.sleepEvent_.isSet():                      # should we sleep?
        time.sleep(1)

