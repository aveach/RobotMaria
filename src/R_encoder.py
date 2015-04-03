#!/usr/bin/env python

### Class to control encoders ###

import Adafruit_BBIO.UART as UART
import serial
import struct
import sensorState

class EncoderController(sensorState.Sensor):
  def __init__(self, inName, inDefaultPriority=3, baudrate = 38400, **kwargs):
    # boilerplate bookkeeping
    sensorState.Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc,
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=3)

    self.baudrate = baudrate

    self.R_encoderPort = "/dev/ttyO2"
    self.R_UART = "UART2"
    UART.setup(self.R_UART)

    self.R_encoderCom = serial.Serial(port = self.R_encoderPort, baudrate = self.baudrate)


  # service the sensor, post the value
  def __threadProc(self, **kwargs):
    while not self.quitEvent_.isSet():                      # should we quit?

        if not self.R_encoderCom.isOpen():
            self.R_encoderCom.open()

        for i in xrange(0, 5):
            self.R_read = self.R_encoderCom.readline().strip()
            if self.R_read.startswith("D"):
                self.R_distance = read[1:]
                self.R_distance = struct.unpack('!i', self.R_distance.decode('hex'))[0]
                self.R_encoderCom.close()
                break
            else:
                pass

        time.sleep(0.1)
        print "\Rear Encoder %s SPEAKS: %s" % (self.name_, self.R_distance)
        self.postReading(self.R_distance, 1)                       # "high" priority

    while self.sleepEvent_.isSet():                      # should we sleep?
        time.sleep(1)
