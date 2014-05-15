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
print "Hello World"
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

# Initialize WayPoint Sensr (GPS, COMPAS)
WayPointSensor = sensorState.WaypointSensor("WaypointSensor")
WayPointSensor.start() 
HeadingDiff = 7

# constants for ramping motors
FromStop = 13
WhileMoving = 5

# Initia; State
MachineState = "PixyScan" #"WayPoint"

# Initialize screen logger message
ScreenLog = screenlogger.ScreenLogger(WayPointSensor.logToScreen, verbose = True)

ScreenLog.Log("Robot Maria is Ready!")

while not QuitFlag:
    time.sleep(0.1) # We will get data every 100 ms
    
    if True: #KillSwitch.getReading().value:
        if MachineState == "PixyScan":
            #Sleep tracking
            PixySensor.sleep()
            time.sleep(0.3)
            ConeStatus = PixySensor.PixyFullScan()
            if ConeStatus:
                MachineState = "PixyTrack"
                ScreenLog.Log("Pixy Scan Found Cone")
            else:
                MachineState = "WayPoint"
                ScreenLog.Log("Pixy Scan Did Not Find Cone")
            PixySensor.wake()
            time.sleep(1)
            
        elif MachineState == "PixyTrack":
            #Get data from pixy and rotate till we are facing the cone.
            ConeAngle = PixySensor.getReading()
            #print "Cone Angle:"+str(ConeAngle)
            #print "Bump State:"+str(Bump.getReading().value)
            if Bump.getReading().value == 1:
                ScreenLog.Log("Bumped Cone")
                Led.allOff()
                Led.turnOn('teal')
                Rover.Stop()
                for i in range(0,FromStop):
                    Rover.Reverse(RotateSpeed)
                    time.sleep(0.1)
                time.sleep(3) 
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
                if ConeAngle.value == None:
                    MachineState = "PixyScan"#"WayPoint"
                    #WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                elif ConeAngle.value > 2:
                    Rover.RotateRight(RotateSpeed)
                    print "Rotate Right"
                    ScreenLog.Log("I see Cone")
                elif ConeAngle.value < -2:
                    print "Rotate Left"
                    Rover.RotateLeft(RotateSpeed)
                    ScreenLog.Log("I see Cone")
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
              for i in range(0,FromStop):
                  Rover.Reverse(RotateSpeed)
                  time.sleep(0.1)
              time.sleep(3) 
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
               if WayPointData["nextWaypoint"] == 0:
                   ScreenLog.Log("Reached last way point.")
                   Led.allOff()
                   Led.turnOn('yellow')
                   Rover.Stop()
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

