# Contains class used to control pololu Motor Controller 18v25 though serial over USB.
# https://www.pololu.com/product/1381

import serial
import time

class MotorController(object):
    def __init__(self, port="/dev/ttyACM0"):
        self.ser=serial.Serial(port = port)
    def exitSafeStart(self):
        ''' When controller first powers up it goes into safe start. We need to exit this mode to start moving.'''
        command = chr(0x83)
        if not self.ser.isOpen():
            self.ser.open()
        self.ser.write(command)
        self.ser.flush()
        #self.ser.close()
    def setSpeed(self, speed):
        ''' Sets motor speed and direction, from -3000 to 3000. '''
        if speed > 0:
            channelByte = chr(0x85)
        else:
            speed = (-1) * speed
            channelByte = chr(0x86)
        lowTargetByte = chr(speed & 0x1F)
        highTargetByte = chr((speed >> 5) & 0x7F)
        command = channelByte + lowTargetByte + highTargetByte
        #if self.ser.isOpen():
        #    self.ser.open()
        self.ser.write(command)
        self.ser.flush()
        #self.ser.close()
    def reset(self):
        self.ser.reset()
    def close(self):
        self.ser.close()
