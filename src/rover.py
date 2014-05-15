# Contains class used to control wheels motion.
import motor
import time


class Rover():
    def __init__(self):
        self.m1 = motor.MotorController('/dev/ttyACM0')
        self.m2 = motor.MotorController('/dev/ttyACM1')
        self.Reset()
        self.speed = 0
        self.accel = 1500
        self.cycle_time = 200 #ms
	self.speed_steps = 100
        self.state = "STOP"
        self.new_state = None
        return

    def Stop(self):
        self.state = "STOP"
        self.m1.setSpeed(0)
        self.m2.setSpeed(0)
        self.speed = 0
        return 

    def __Move__(self, speed, m1dir, m2dir):
	if (self.new_state == self.state) and (speed == self.speed):
            print "Dont update, speed and direction are the same as before"
            return True
        if self.new_state != self.state:
            if (self.new_state == "REVERSE") or (self.state == "REVERSE"):
                self.Stop()
            self.state = self.new_state
            self.speed = int(speed/2)
            return

        # Makes sure speed is between 0-3200
        if speed > 3200:
            speed = 3200
        elif speed < 0:
            speed = 0
        # Ramp up speed
        if self.state != "STOP":
            print "Target speed: "+str(speed)+" Current Speed:"+str(self.speed)
            if speed < self.speed:
                self.sign = -1
            elif speed > self.speed:
                self.sign = 1
            self.speed_diff = abs(speed-self.speed)
            if self.speed_diff < 50:
                self.speed += self.sign * self.speed_diff
            else:
                self.speed += self.sign * self.speed_steps
            self.m1.setSpeed(int((m1dir)*self.speed))
            self.m2.setSpeed(int((m2dir)*self.speed))
            
        return True
      
    def Forward(self, speed):
        self.new_state = "FORWARD"
        return self.__Move__(speed,m1dir=1, m2dir=-1)
        

    def Reverse(self, speed):
        self.new_state = "REVERSE"
        return self.__Move__(speed,m1dir=-1,m2dir=1)
        

    def RotateRight(self, speed):
        self.new_state = "RIGHT"
        return self.__Move__(speed,m1dir=1,m2dir=-0.3)
        

    def RotateLeft(self, speed):
        self.new_state = "LEFT"
        return self.__Move__(speed,m1dir=0.3,m2dir=-1)
        

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
