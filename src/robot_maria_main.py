#!/usr/bin/env python
''' main code here '''

import sensorState
import rover
import pixyTracker
import time

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
    if ConeAngle > 2:
        #Rover.RotateRight(RotateSpeed)
    elif ConeAngle < -2:
        #Rover.RotateLeft(Rotate Speed)
    else:
        print "We found the Cone !!! Pixy Residual Angle:"+str(ConeAngle)
    

