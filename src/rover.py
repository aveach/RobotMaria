# Contains class used to control wheels motion.
import motor
import time

class Rover():
    def __init__(self):
        self.m1 = motor.MotorController('/dev/tty.usbmodem14111')
        self.m2 = motor.MotorController('/dev/tty.usbmodem14121')
        self.Reset()
        self.speed = 0
        return

    def Stop(self):
        self.m1.setSpeed(0)
        self.m2.setSpeed(0)
        self.speed = 0
        return 

    def Forward(self, speed):
        self.speed = speed
        self.m1.setSpeed(self.speed)
        self.m2.setSpeed((-1)*self.speed)
        return

    def Reverse(self, speed):
        self.speed = speed
        self.m1.setSpeed((-1)*self.speed)
        self.m2.setSpeed(self.speed)
        return

    def RotateRight(self, speed):
        self.speed = speed
        self.m1.setSpeed(self.speed)
        self.m2.setSpeed(self.speed)
        return

    def RotateLeft(self, speed):
        self.speed = speed
        self.m1.setSpeed((-1)*self.speed)
        self.m2.setSpeed((-1)*self.speed)
        return

    def Reset(self):
        self.m1.exitSafeStart()
        self.m2.exitSafeStart()
        self.Stop()
        return
