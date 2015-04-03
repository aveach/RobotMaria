#!/usr/bin/env python
''' main code here '''

import sensorState
import rover
import pixyTracker
import time
import signal
import rgb
import bump
import wifiswitch

QuitFlag = False

# Ctrl-c handler
def ctrlC(signal, frame):
    global Quitflag
    PixySensor.quit()
    Rover.Stop()
    QuitFlag = True

signal.signal(signal.SIGINT,ctrlC)

# Initialize rover
Rover = rover.Rover()
RotateSpeed = 3200

#Initialize LED
Led = rgb.RGBController()

#Initialize Bump Sensor
Bump = bump.BumpSensor("BumpSensor")
Bump.start(None)

#Initialize Wifi Kill Switch
KillSwitch = wifiswitch.WifiSwitch("KillSwitch", host_ip = "172.20.10.1")
KillSwitch.start()

# Initialize Pixy
#PixySensor = pixyTracker.pixyController('pixy')
#PixySensor.start(None)

# Initialize WayPoint Sensr (GPS, COMPAS)
WayPointSensor = sensorState.WaypointSensor("WaypointSensor")
WayPointSensor.start() 
HeadingDiff = 7

# Initia; State
MachineState = "WayPoint"

# Initialize screen logger message
ScreenLog = screenlogger.ScreenLogger(WayPointSensor.logToScreen, verbose = True)

ScreenLog.Log("Robot Maria is Ready!")

while not QuitFlag:
    time.sleep(0.1) # We will get data every 100 ms
    
    if KillSwitch.getReading().value:
        if MachineState == "Pixy":
            #Get data from pixy and rotate till we are facing the cone.
            ConeAngle = PixySensor.getReading()
            #print "Cone Angle:"+str(ConeAngle)
            #print "Bump State:"+str(Bump.getReading().value)
            if Bump.getReading().value == 1:
                ScreenLog.Log("Bumped Cone")
                Led.allOff()
                Led.turnOn('teal')
                Rover.Stop()
            else:
                Led.allOff()
                Led.turnOn('purple')
                if ConeAngle.value > 2:
                    Rover.RotateRight(RotateSpeed)
                    print "Rotate Right"
                elif ConeAngle.value < -2:
                    print "Rotate Left"
                    Rover.RotateLeft(RotateSpeed)
                else:
                    Rover.Forward(RotateSpeed)
                    print "Forward, Pixy Residual Angle:"+str(ConeAngle)

        elif MachineState == "WayPoint":
           WayPointData = WayPointSensor.getReading().value
           if Bump.getReading().value == 1:
              ScreenLog.Log("Bumped into something")
              Led.allOff()
              Led.turnOn('teal')
			  # Time to avoid the obstacle by reversing, 
			  # turning right moving forward and turning back left again
              Rover.Stop()    
              Rover.Reverse(RotateSpeed)
              time.sleep(3) 
              Rover.Stop()    
              Rover.RotateRight(RotateSpeed)
              time.sleep(3) 
              Rover.Stop()    
              Rover.Forward(RotateSpeed)
              time.sleep(3) 
              Rover.Stop()    
              Rover.RotateLeft(RotateSpeed)
              time.sleep(3) 
              Rover.Stop()    

           elif WayPointData != None:
               if WayPointData["nextWaypoint"] == 0:
                   ScreenLog.Log("Reached last way point.")
                   Led.allOff()
                   Led.turnOn('yellow')
                   Rover.Stop()
               else: 
                   if (WayPointData["currentHorizontalAccuracy"]+2 < 2) and (WayPointData["distanceToNextWaypoint"] < (WayPointData["currentHorizontalAccuracy"]+2)):
                       #print "We are close to cone, switch to Pixy. Distance: "+str(WayPointData["distanceToNextWaypoint"])
                       ScreenLog.Log("Reached Waypoint: "+str(WayPointData["nextWaypoint"])
                       ScreenLog.Log("Close to Cone, switching to Pixy Mode.")
                       Rover.Stop()
                       Led.allOff()
                       Led.turnOn('green')
                       time.sleep(0.5)
                       WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                   elif WayPointData["distanceToNextWaypoint"] <= 2: 
                       #print "We are close to cone, switch to Pixy. Distance: "+str(WayPointData["distanceToNextWaypoint"])
                       ScreenLog.Log("Reached Waypoint: "+str(WayPointData["nextWaypoint"])
                       ScreenLog.Log("Close to Cone, switching to Pixy Mode.")
                       Rover.Stop()
                       Led.allOff()
                       Led.turnOn('green')
                       time.sleep(0.5)
                       WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                   else:
                       Led.allOff()
                       Led.turnOn('blue')
                       if WayPointData["currentHorizontalAccuracy"] < 5000:#20:
                           AngleDiff = WayPointData["headingToNextWaypoint"] - WayPointData["direction"]
                           if (AngleDiff < -180):
                               AngleDiff += 360
                           elif (AngleDiff > 180):
                               AngleDiff -= 360
                           #print "AngleDiff: "+str(AngleDiff) 
                           # Allow a small degree of diviation before taking action
                           if abs(AngleDiff) > HeadingDiff:
                               if AngleDiff > 0:
                                   Rover.RotateRight(RotateSpeed)
                                   print "ROTATE RIGHT"
                               else:
                                   Rover.RotateLeft(RotateSpeed)
                                   print "ROTATE LEFT"
                           else:
                                   Rover.Forward(RotateSpeed)
                                   print "FORWARD"
           else:
               #print "Waypoint data is None"
               ScreenLog.Log("WayPoint data is None")                
               Led.allOff()
               Led.turnOn('red')
    else:
        ScreenLog.Log("Kill Switch enabled.")
        Led.allOff()
        Led.turnOn('red')
