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

        read_one = self.encoderCom.readline().strip()
        read_two = self.encoderCom.readline().strip()
            if read_one.startswith("D"):
                value = read_one[1:]
                value = struct.unpack('!i', value.decode('hex'))[0]
                self.encoderCom.close()
                return value
            elif read_two.startswith("D"):
                value = read_two[1:]
                value = struct.unpack('!i', value.decode('hex'))[0]
                self.encoderCom.close()
                return value
            else:
                return 0

    def getVelocity(self):
        if not seld.encoderCom.isOpen():
            self.encoderCom.open()

        read_one = self.encoderCom.readline().strip()
        read_two = self.encoderCom.readline().strip()
            if read_one.startswith("V"):
                value = read_one[1:]
                value = int(value, 16)
                self.encoderCom.close()
                return value
            elif read_two.startswith("V"):
                value = read_two[1:]
                value = int(value, 16)
                self.encoderCom.close()
                return value
            else:
                return 0

    def close(self):
        self.encoderCom.close()
