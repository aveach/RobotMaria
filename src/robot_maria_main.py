#!/usr/bin/env python
''' main code here '''

import sensorState
import rover
import pixyTracker
import time
import signal

# Ctrl-c handler
def ctrlC():
    PixySensor.quit()
    Rover.Stop()

signal.signal(signal.SIGINT,ctrlC)

# Initialize rover
Rover = rover.Rover()
RotateSpeed = 1000

# Initialize sensorState
#SensorState = sensorState.SensorState()
#SensorState.start()

# Initialize Pixi
PixySensor = pixyTracker.pixyController('pixy')
PixySensor.start(None)
#sensorState.registerSensor(PixySensor)

while 1:
    time.sleep(0.1) # We will get data from pixy every 100 ms

    #Get data from pixy and rotate till we are facing the cone.
    ConeAngle = PixySensor.getReading()
    print "Cone Angle:"+str(ConeAngle)
    if ConeAngle.value > 2:
        Rover.RotateRight(RotateSpeed)
        print "Rotate Right"
    elif ConeAngle.value < -2:
        print "Rotate Left"
        Rover.RotateLeft(RotateSpeed)
    else:
        print "We found the Cone !!! Pixy Residual Angle:"+str(ConeAngle)
        Rover.Stop()
    

