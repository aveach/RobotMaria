#!/usr/bin/env python
''' main code here '''

import sensorState
import rover
import pixyTracker
import time
import signal


# Ctrl-c handler
def ctrlC(signal, frame):
    PixySensor.quit()
    Rover.Stop()

signal.signal(signal.SIGINT,ctrlC)

# Initialize rover
Rover = rover.Rover()
RotateSpeed = 3200


# Initialize Pixy
PixySensor = pixyTracker.pixyController('pixy')
PixySensor.start(None)

# Initialize WayPoint Sensr (GPS, COMPAS)
WayPointSensor = sensorState.WaypointSensor("WaypointSensor")
WayPointSensor.start() 
HeadingDiff = 7

# Initia; State
MachineState = "WayPoint"

while True:
    time.sleep(0.1) # We will get data every 100 ms

    if MachineState == "Pixy":
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
            Rover.Forward(RotateSpeed)
            #print "We found the Cone !!! Pixy Residual Angle:"+str(ConeAngle)
            Rover.Stop()
    

    if MachineState == "WayPoint":
       WayPointData = WayPointSensor.getReading().value
       if WayPointData["distanceToNextWaypoint"] <= 12:
           print "We are close to cone, switch to Pixy. Distance: "+str(WayPointData["distanceToNextWaypoint"]) 
       else:
           if WayPointData["currentHorizontalAccuracy"] < 20:
               AngleDiff = WayPointData["headingToNextWaypoint"] - WayPointData["direction"]
               if (AngleDiff < -180):
                   AngleDiff += 360
               elif (AngleDiff > 180):
                   AngleDiff -= 360
               
               # Allow a small degree of diviation before taking action
               if abs( 
