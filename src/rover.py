# Contains class used to control wheels motion.
import motor
import time

class Rover():
    def __init__(self):
        self.m1 = motor.MotorController('/dev/ttyACM0')
        self.m2 = motor.MotorController('/dev/ttyACM1')
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

if __name__ == "__main__":
	import curses
	
	#Initialize Motors
	rover = Rover()
	speed = 1000
	# get the curses screen window
	screen = curses.initscr()

	# turn off input echoing
	curses.noecho()

	# respond to keys immediately (don't wait for enter)
	curses.cbreak()

	# map arrow keys to special values
	screen.keypad(True)

	try:
   		while True:
			char = screen.getch()
			if char == ord('q'):
				break
			elif char == curses.KEY_RIGHT:
				# print doesn't work with curses, use addstr instead
				screen.addstr(0, 0, 'right')
				rover.RotateRight(speed)
			elif char == curses.KEY_LEFT:
				screen.addstr(0, 0, 'left ')
				rover.RotateLeft(speed)
			elif char == curses.KEY_UP:
				screen.addstr(0, 0, 'up   ')
				rover.Forward(speed)
			elif char == curses.KEY_DOWN:
				screen.addstr(0, 0, 'down ')
				rover.Reverse(speed)
			elif char == ord('>'):
				speed +=100
				screen.addstr(0,0, 'speed '+str(speed))
			elif char == ord('<'):
				speed -=100
				screen.addstr(0,0, 'speed '+str(speed))
			else:
				screen.addstr(0,0, 'stop ')
				rover.Stop()
	finally:
    	# shut down cleanly
		curses.nocbreak(); screen.keypad(0); curses.echo()
		curses.endwin()	
