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
import screenlogger
import sys

QuitFlag = False
BumpDone = False

# Ctrl-c handler
def ctrlC(signal, frame):
    global QuitFlag
    PixySensor.quit()
    Rover.Stop()
    WayPointSensor.quit()    
    Bump.quit()
    QuitFlag = True
    time.sleep(2)
    sys.exit(0)

signal.signal(signal.SIGINT,ctrlC)
signal.signal(signal.SIGABRT,ctrlC)

# Initialize rover
Rover = rover.Rover()
RotateSpeed = 3200

#Initialize LED
Led = rgb.RGBController()

#Initialize Bump Sensor
Bump = bump.BumpSensor("BumpSensor")
Bump.start()

#Initialize Wifi Kill Switch
KillSwitch = wifiswitch.WifiSwitch("KillSwitch", host_ip = "172.20.10.1")
#KillSwitch.start()

# Initialize Pixy
PixySensor = pixyTracker.pixyController('pixy')
PixySensor.start()
PixyTimeCounter = 0
MAX_HUNT_TIME = 1800 #180 seconds
HuntCounter = 0

# Initialize WayPoint Sensr (GPS, COMPAS)
WayPointSensor = sensorState.WaypointSensor("WaypointSensor")
WayPointSensor.start() 
HeadingDiff = 7

# constants for ramping motors
FromStop = 13
WhileMoving = 5

# Initia; State
MachineState = "PixyScan"#"WayPoint"

# Initialize screen logger message
ScreenLog = screenlogger.ScreenLogger(WayPointSensor.logToScreen, verbose = True)

ScreenLog.Log("Robot Maria is Ready!")

while not QuitFlag:
    time.sleep(0.1) # We will get data every 100 ms
    
    if True: #KillSwitch.getReading().value:
        if MachineState == "PixyScan":
            HuntCounter += 1
            #Sleep tracking
            PixySensor.sleep()
            time.sleep(0.3)
            for i in range(2):
                ConeStatus = PixySensor.PixyFullScan()
                if ConeStatus:
                    MachineState = "PixyTrack"
                    TrackCountCounter = 0 
                    ScreenLog.Log("Pixy Scan Found Cone")
                elif i < 1:
                    for n in range(13):
                        Rover.RotateRight(RotateSpeed)
                        time.sleep(0.2)
                    Rover.Stop() 
                else:
                    MachineState = "WayPoint"
                    WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                    ScreenLog.Log("Pixy Scan Did Not Find Cone")
            PixySensor.wake()
            time.sleep(1)
            
        elif MachineState == "PixyTrack":
            HuntCounter +=1
            #Get data from pixy and rotate till we are facing the cone.
            ConeAngle = PixySensor.getReading()
            #print "Cone Angle:"+str(ConeAngle)
            #print "Bump State:"+str(Bump.getReading().value)
            if Bump.getReading().value == 1:
                ScreenLog.Log("Bumped Cone")
                BumpDone = True
                Led.allOff()
                Led.turnOn('teal')
                Rover.Stop()
                for i in range(0,FromStop):
                    Rover.Reverse(RotateSpeed)
                    time.sleep(0.1)
                time.sleep(2) 
                Rover.Stop()    
                for i in range(0,FromStop):
                    Rover.RotateRight(RotateSpeed)
                    time.sleep(0.1) 
                time.sleep(2) 
                for i in range(0,WhileMoving):
                    Rover.Forward(RotateSpeed)
                    time.sleep(0.1) 
                time.sleep(2)
                for i in range(0,WhileMoving):
                    Rover.RotateLeft(RotateSpeed)
                    time.sleep(0.1)
                time.sleep(2) 
                Rover.Stop()    
                MachineState = "WayPoint"
                WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
            else:
                Led.allOff()
                Led.turnOn('purple')
                if (ConeAngle.value == None) and (PixyTimeCounter > 20) :
                     
                    Rover.Stop()
                    if HuntCounter >= MAX_HUNT_TIME:
                        MachineState = "WayPoint"
                        WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                    else:
                        MachineState = "PixyScan"
                elif ConeAngle.value > 2:
                    Rover.RotateRight(RotateSpeed)
                    print "Rotate Right"
                    ScreenLog.Log("I see Cone")
                    PixyTimeCounter = 0
                elif ConeAngle.value < -2:
                    print "Rotate Left"
                    Rover.RotateLeft(RotateSpeed)
                    ScreenLog.Log("I see Cone")
                    PixyTimeCounter = 0
                elif ConeAngle.value != None:
                    Rover.Forward(RotateSpeed)
                    PixyTimeCounter = 0
                    print "Forward, Pixy Residual Angle:"+str(ConeAngle)
            PixyTimeCounter += 1

        elif MachineState == "WayPoint":
           WayPointData = WayPointSensor.getReading().value
           if Bump.getReading().value == 1:
              ScreenLog.Log("Bumped into something")
              Led.allOff()
              Led.turnOn('teal')
              # Time to avoid the obstacle by reversing, 
              # turning right moving forward and turning back left again
              Rover.Stop()
              for i in range(0,FromStop):
                  Rover.Reverse(RotateSpeed)
                  time.sleep(0.1)
              time.sleep(2) 
              Rover.Stop()    
              for i in range(0,FromStop):
                  Rover.RotateRight(RotateSpeed)
                  time.sleep(0.1)
              time.sleep(2) 
              for i in range(0,WhileMoving):
                  Rover.Forward(RotateSpeed)
                  time.sleep(0.1)
              time.sleep(2) 
              for i in range(0,WhileMoving):
                  Rover.RotateLeft(RotateSpeed)
                  time.sleep(0.1)
              time.sleep(2) 
              Rover.Stop()    

           elif WayPointData != None:
               while (WayPointData["nextWaypointWeight"] == 1) and BumpDone:
                   WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                   WayPointData = WayPointSensor.getReading().value
               BumpDone = False

               ConeAngle = PixySensor.getReading()
               if WayPointData["nextWaypoint"] == 0:
                   ScreenLog.Log("Reached last way point.")
                   Led.allOff()
                   Led.turnOn('yellow')
                   Rover.Stop()
               #elif (ConeAngle != None) and (WayPointData["nextWaypointWeight"] == 1):
               #    Rover.Stop()
               #    MachineState = "PixyTrack" 
               else: 
                   if (WayPointData["currentHorizontalAccuracy"]+2 < 2) and (WayPointData["distanceToNextWaypoint"] < (WayPointData["currentHorizontalAccuracy"]+2)):
                       #print "We are close to cone, switch to Pixy. Distance: "+str(WayPointData["distanceToNextWaypoint"])
                       ScreenLog.Log("Reached Waypoint: "+str(WayPointData["nextWaypoint"]))
                       ScreenLog.Log("Close to Cone, switching to Pixy Mode.")
                       Rover.Stop()
                       Led.allOff()
                       Led.turnOn('green')
                       time.sleep(0.5)
                       if WayPointData["nextWaypointWeight"] == 1:
                           MachineState = "PixyScan"
                           HuntCounter = 0
                           PixyTimeCounter = 0
                       else:
                           WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                   elif WayPointData["distanceToNextWaypoint"] <= 2: 
                       #print "We are close to cone, switch to Pixy. Distance: "+str(WayPointData["distanceToNextWaypoint"])
                       ScreenLog.Log("Reached Waypoint: "+str(WayPointData["nextWaypoint"]))
                       ScreenLog.Log("Close to Cone, switching to Pixy Mode.")
                       Rover.Stop()
                       Led.allOff()
                       Led.turnOn('green')
                       time.sleep(0.5)
                       if WayPointData["nextWaypointWeight"] == 1:
                           MachineState = "PixyScan"
                           PixyTimeCounter = 0
                       else:
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
sys.exit(0)

