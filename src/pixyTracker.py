#!/usr/bin/env python

### Class to control the RGB LED Indicator ###

import sys
import signal
import sensorState
sys.path.append("/home/debian/pixy/build/pantilt_in_python")
from pixy import *
from ctypes import *
import time

PIXY_MIN_X             =    0
PIXY_MAX_X             =  319

PIXY_X_CENTER          =  ((PIXY_MAX_X-PIXY_MIN_X) / 2)
PIXY_RCS_MIN_POS       =    0
PIXY_RCS_MAX_POS       = 1000
PIXY_RCS_CENTER_POS    =  ((PIXY_RCS_MAX_POS-PIXY_RCS_MIN_POS) / 2)

PIXY_RCS_PAN_CHANNEL   =    0

PAN_PROPORTIONAL_GAIN  =  400
PAN_DERIVATIVE_GAIN    =  800

BLOCK_BUFFER_SIZE      =    1


class Blocks (Structure):
  _fields_ = [ ("type", c_uint),
               ("signature", c_uint),
               ("x", c_uint),
               ("y", c_uint),
               ("width", c_uint),
               ("height", c_uint),
               ("angle", c_uint) ]

class Gimbal ():
  _fields_ = [ ("position", c_uint),
               ("first_update", bool),
               ("previous_error", c_uint),
               ("proportional_gain", c_uint),
               ("derivative_gain", c_uint) ]

  def __init__(self, start_position, proportional_gain, derivative_gain):
    self.position          = start_position
    self.proportional_gain = proportional_gain
    self.derivative_gain   = derivative_gain
    self.previous_error    = 0
    self.first_update      = True

  def update(self, error):
    if self.first_update == False:
      error_delta = error - self.previous_error
      P_gain      = self.proportional_gain;
      D_gain      = self.derivative_gain;

      # Using the proportional and derivative gain for the gimbal #
      # calculate the change to the position                      #
      velocity = (error * P_gain + error_delta * D_gain) / 1024;

      self.position += velocity;

      if self.position > PIXY_RCS_MAX_POS:
        self.position = PIXY_RCS_MAX_POS
      elif self.position < PIXY_RCS_MIN_POS:
        self.position = PIXY_RCS_MIN_POS
    else:
      self.first_update = False

    self.previous_error = error


class pixyController(sensorState.Sensor):
  def __init__(self, inName, inDefaultPriority=3, **kwargs):
    # boilerplate bookkeeping
    sensorState.Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc,
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=3)

    # Initialize Pixy Interpreter thread #
    self.pixy_init_status = pixy_init()

    if self.pixy_init_status != 0:
      pixy_error(self.pixy_init_status)
      print "Pixy failed to initialize"
      return

    #  Initialize Gimbals #
    self.pan_gimbal = Gimbal(PIXY_RCS_CENTER_POS, PAN_PROPORTIONAL_GAIN, PAN_DERIVATIVE_GAIN)

    # Initialize block #
    self.block = Block()

  def PixyFullScan(self):
    # Doesn't work need further investigation on how the servo is controlled.
    self.scan_step = int(319/5)
    self.raw_position = 0
    self.count = 0
    while (self.raw_position < 320) or (self.count > 0):
        self.pan_gimbal.update(self.raw_position)
        time.sleep(1)
        self.count = pixy_get_blocks(BLOCK_BUFFER_SIZE, self.block)
        self.raw_position += self.scan_step
        
    
    if self.count > 0:
        print "Found cone while scanning. Position:"+str(self.raw_position-self.scan_step)

  # service the sensor, post the value
  def __threadProc(self, **kwargs):
    myReading = None
    while not self.quitEvent_.isSet():                     # should we quit?

      # Grab a block #
      self.count = pixy_get_blocks(BLOCK_BUFFER_SIZE, self.block)

      # Was there an error? #
      if self.count < 0:
        print 'Error: pixy_get_blocks()'
        pixy_error(self.count)
        sys.exit(1)

      if self.count > 0:
        # We found a block #

        # Calculate the difference between Pixy's center of focus #
        # and the target.
        #print "Pixy Center: {} -- X Block: {}".format(PIXY_X_CENTER, block.x)                                         #
        self.pan_error  = PIXY_X_CENTER - self.block.x

        # Apply corrections to the pan/tilt gimbals with the goal #
        # of putting the target in the center of Pixy's focus.    #
        self.pan_gimbal.update(self.pan_error)
        self.servo_position = (1024-self.pan_gimbal.position)*(180/1024.0)-90
        #print "Pixy object found at {} degrees".format(self.servo_position)

        set_position_result = pixy_rcs_set_position(PIXY_RCS_PAN_CHANNEL, self.pan_gimbal.position)

        if set_position_result < 0:
          print 'Error: pixy_rcs_set_position() '
          pixy_error(result)
          sys.exit(2)
        
        myReading = (1024-self.pan_gimbal.position)*(180/1024.0)-90                # ZarkonSensor takes one parameter, incrementBy
      else:
        # We want to know if no blocks were found, we will return None instead of servo position.
        myReading = None
      print "\Pixy %s SPEAKS: %s" % (self.name_, myReading)
      self.postReading(myReading, 1)                       # "high" priority
      time.sleep(0.2)
      while self.sleepEvent_.isSet():                      # should we sleep?
        time.sleep(0.5)
    pixy_close()
