#!/usr/bin/env python

### Class to control encoders ###

import Adafruit_BBIO.UART as UART
import serial
import struct


class EncoderController(object):
    def __init__(self, port="/dev/ttyO4", baudrate=38400, UART):
        UART.setup(UART)
        self.encoderCom = serial.Serial(port=port, baudrate=baudrate)
        self.encoderCom.close()

    def getDistance(self):
        if not self.encoderCom.isOpen():
            self.encoderCom.open()

        for i in xrange(0, 10):
            read = self.encoderCom.readline().strip()
            if read.startswith("D"):
                value = read[1:]
                value = struct.unpack('!i', value.decode('hex'))[0]
                self.encoderCom.close()
                break
            else:
                pass
        return value

    def getVelocity(self):
        if not self.encoderCom.isOpen():
            self.encoderCom.open()

        for i in xrange(0, 10):
            read = self.encoderCom.readline().strip()
            if read.startswith("V"):
                value = read[1:]
                value = int(value, 16)
                self.encoderCom.close()
                break
            else:
                pass
        return value

    def close(self):
        self.encoderCom.close()
