#!/usr/bin/env python

### Class to receive Sonar data ###

import Adafruit_BBIO.UART as UART
import serial


class SonarController(object):
    def __init__(self, port="/dev/ttyO5", baudrate=9600, UART):
        UART.setup(UART)
        self.sonarCom = serial.Serial(port=port, baudrate=baudrate)
        self.sonarCom.close()

    def getDistance(self):
        if not self.sonarCom.isOpen():
            self.sonarCom.open()

        for i in xrange(0, 10):
            read = self.sonarCom.readline().strip()
            if read.startswith("R"):
            # Strip off the leading "R"
                value = read[1:]
                value = struct.unpack('!i', value.decode('hex'))[0]
                self.sonarCom.close()
                break
            else:
                pass
        return value


    def close(self):
        self.sonarCom.close()

