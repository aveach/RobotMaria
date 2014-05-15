# Contains class used to control wheels motion.
import motor
import time

class MotorEmulate():
    def __init__(self):
        return
    def setSpeed(self,speed):
        print speed
        return

class Rover():
    def __init__(self, emulate = False):
        if not emulate:
            self.m1 = motor.MotorController('/dev/ttyACM0')
            self.m2 = motor.MotorController('/dev/ttyACM1')
            self.Reset()
        else:
            self.m1 = MotorEmulate()
            self.m2 = MotorEmulate()
        self.speed = [0,0]
        self.accel = 1500
        self.cycle_time = 200 #ms
        self.speed_steps = 800
        self.speed_steps_stop = 100
        self.state = "STOP"
        self.new_state = None
        return

    def Stop(self):
        self.state = "STOP"
        self.m1.setSpeed(0)
        self.m2.setSpeed(0)
        self.speed = [0,0]
        return 

    def __Move__(self, speed, m1dir, m2dir):
        # Makes sure speed is between 0-3200
        if speed > 3200:
            speed = 3200
        elif speed < 0:
            speed = 0
        
        new_speed = [int(speed*m1dir),int(speed*m2dir)] 
        #print "New State: "+self.new_state+" New Speed: "+str(new_speed)
        if (self.new_state == self.state) and (new_speed == self.speed):
            #print "Dont update, speed and direction are the same as before"
            return True
        
        if (self.new_state != self.state) and (self.state != "STOP") and ((self.new_state == "REVERSE") or (self.state == "REVERSE")):
            self.Stop()
            #print "Stop first from or to reverse"
            return True
 
        # Ramp up/down speed
        if self.new_state != "STOP":
            #print "Target speed: "+str(speed)+" Current Speed:"+str(self.speed)
            self.state = self.new_state
            for i in range(len(self.speed)):
                if new_speed[i] < self.speed[i]:
                    self.sign = -1
                elif new_speed[i] > self.speed[i]:
                    self.sign = 1
                self.speed_diff = abs(new_speed[i]-self.speed[i])
                if self.speed_diff < self.speed_steps:
                    self.speed[i] += self.sign * self.speed_diff
                elif self.speed_diff >= self.speed_steps:
                    if self.speed < 1000:
                       self.speed[i] += self.sign * self.speed_steps_stop
                    else:
                       self.speed[i] += self.sign * self.speed_steps
            self.m1.setSpeed(self.speed[0])
            self.m2.setSpeed(self.speed[1])
            
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
