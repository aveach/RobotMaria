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

    self.F_encoderPort = "/dev/ttyO1"
    self.F_UART = "UART1"
    UART.setup(self.F_UART)

    self.F_encoderCom = serial.Serial(port = self.F_encoderPort, baudrate = self.baudrate)


  # service the sensor, post the value
  def __threadProc(self, **kwargs):
    while not self.quitEvent_.isSet():                      # should we quit?

        if not self.F_encoderCom.isOpen():
            self.F_encoderCom.open()

        for i in xrange(0, 5):
            self.F_read = self.F_encoderCom.readline().strip()
            if self.F_read.startswith("D"):
                self.F_distance = read[1:]
                self.F_distance = struct.unpack('!i', self.F_distance.decode('hex'))[0]
                self.F_encoderCom.close()
                break
            else:
                pass

        time.sleep(0.1)
        print "\Front Encoders %s SPEAKS: %s" % (self.name_, self.F_distance)
        self.postReading(self.F_distance, 1)                       # "high" priority

    while self.sleepEvent_.isSet():                      # should we sleep?
        time.sleep(1)
