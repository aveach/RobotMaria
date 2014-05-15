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
#KillSwitch = wifiswitch.WifiSwitch("KillSwitch", host_ip = "172.20.10.1")
#KillSwitch.start()

# Initialize Pixy
PixySensor = pixyTracker.pixyController('pixy')
PixySensor.start()
PixyTimeCounter = 0
PIXY_DRIVE_LIMIT = 50 # seconds x 10
PIXY_ANGLE_TOLERANCE = 2
MAX_HUNT_TIME = 1800 #180 seconds
PixyCompassHeading = 0


# Initialize WayPoint Sensr (GPS, COMPAS)
WayPointSensor = sensorState.WaypointSensor("WaypointSensor")
WayPointSensor.start() 
HeadingDiff = 3 #7
ConeWayPointBuffer = []
MAX_CONE_TIME = 3000 # (Min x 60)/0.1 
ConeTimer = 0
CurrentWayPoint = 0

# constants for ramping motors
FromStop = 7
WhileMoving = 5

# Initia; State
MachineState = "WayPoint"

# Initialize screen logger message
ScreenLog = screenlogger.ScreenLogger(WayPointSensor.logToScreen, verbose = True)

ScreenLog.Log("Robot Maria is Ready!")

def AvoidObstacle():
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
    return

def SkipCurrentCone():
    WayPointData = WayPointSensor.getReading().value
    while WayPointData["nextWaypointWeight"] > 0: 
        WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
	time.sleep(0.3)
    return


# =====  MAIN LOOP  =====

while not QuitFlag:
    time.sleep(0.1) # We will get data every 100 ms
    # Read pixy, GPS/Compas every cycle
    ConeAngle = PixySensor.getReading()
    WayPointData = WayPointSensor.getReading().value
    if WayPointData != None:
        if WayPointData["killSwitch"] == 0:
            if len(ConeWayPointBuffer) > 0: # We are currently in an area near a cone
                if ConeTimer > MAX_CONE_TIME*WayPointData["nextWaypointWeight"]:
                    SkipCurrentCone()
                    ConeWayPointBuffer = []
                    MachineState = "WayPoint"
                    ScreenLog.Log("MAX_CONE_TIME expired")
                else:
                    ConeTimer += 1

            if MachineState == "PixyScan":
                #Sleep tracking
                PixySensor.sleep()
                time.sleep(0.3)
                for i in range(2):
                    ConeStatus = PixySensor.PixyFullScan()
                    if ConeStatus:
                        MachineState = "PixyTrack"
                        PixyTimeCounter = 0
                        TrackCountCounter = 0 
                        ScreenLog.Log("Pixy Scan Found Cone")
                    elif i < 1:
                        # Do a 180 Degree turn right
                        for n in range(13):
                            Rover.RotateRight(RotateSpeed)
                            time.sleep(0.3)
                        Rover.Stop() 
                    else:
                        MachineState = "WayPoint"
                        if WayPointData["nextWaypointWeight"] > 0:
                            ConeWayPointBuffer.append(WayPointData)
                        WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                        #WayPointData = WayPointSensor.getReading().value
                        #See if we need to retry cone waypoints
                        #if (len(ConeWayPointBuffer) > 0) and (WayPointData["nextWaypointWeight"] == 0):
                        #    WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]-len(ConeWayPointBuffer)) 
                        ScreenLog.Log("Pixy Scan Did Not Find Cone")
                PixySensor.wake()
                time.sleep(1)
            #########################################
            #           PIXY TRACKING               #
            #########################################
            elif MachineState == "PixyTrack":
                #Drive using Pixy data or previous known heading from pixy and rotate till we are facing the cone.
                if Bump.getReading().value == 1:
                    ScreenLog.Log("Bumped Cone")
                    Led.allOff()
                    Led.turnOn('teal')
                    AvoidObstacle()
                    MachineState = "WayPoint"
                    if PixyTimeCounter < 10: # Pixy tracked the cone 1s before bumping something, but it was done with compass driving.
                        SkipCurrentCone()
                    else:
                        if WayPointData["nextWaypointWeight"] > 0:
                            ConeWayPointBuffer.append(WayPointData)
                        WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                        #time.sleep(0.5) # Need to allow WayPoint thread run to update value
                        #WayPointData = WayPointSensor.getReading().value
                        #See if we need to retry cone waypoints
                        #if (len(ConeWayPointBuffer) > 0) and (WayPointData["nextWaypointWeight"] == 0):
                        #    WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]-len(ConeWayPointBuffer)) 

                else:
                    Led.allOff()
                    Led.turnOn('purple')
                    if (ConeAngle.value == None) and (PixyTimeCounter > PIXY_DRIVE_LIMIT) :
                        Rover.Stop()
                        MachineState = "WayPoint"
                        if WayPointData["nextWaypointWeight"] > 0:
                            ConeWayPointBuffer.append(WayPointData)
                        WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                    else:
                        # Lets decide if pixy or compass should drive the rover
                        if ConeAngle.value != None:  # Pixy Drives
                            ScreenLog.Log("Pixy Drives: I see a Cone")
                            PixyTimeCounter = 0
                            # Lets record pixy orientation relative to compass
                            PixyCompassHeading = WayPointData["direction"] + ConeAngle.value
                            if PixyCompassHeading > 360:
                                PixyCompassHeading -= 360
                            elif PixyCompassHeading < 0:
                                PixyCompassHeading += 360
        
                            if ConeAngle.value > PIXY_ANGLE_TOLERANCE:
                                Rover.RotateRight(RotateSpeed)
                                print "Rotate Right"
                            elif ConeAngle.value < (-1)*PIXY_ANGLE_TOLERANCE:
                                print "Rotate Left"
                                Rover.RotateLeft(RotateSpeed)
                            else:
                                Rover.Forward(RotateSpeed)
                                print "Forward, Pixy Residual Angle:"+str(ConeAngle.value)
                        else: # Compass Drives
                                PixyTimeCounter += 1
                                ScreenLog.Log("Compass Driving to Cone")
                                AngleDiff = PixyCompassHeading - WayPointData["direction"] 
                                if (AngleDiff < -180):
                                    AngleDiff += 360
                                elif (AngleDiff > 180):
                                    AngleDiff -= 360
                                # Allow a small degree of diviation before taking action
                                if abs(AngleDiff) > PIXY_ANGLE_TOLERANCE:
                                    if AngleDiff > 0:
                                        Rover.RotateRight(RotateSpeed)
                                        print "ROTATE RIGHT"
                                    else:
                                        Rover.RotateLeft(RotateSpeed)
                                        print "ROTATE LEFT"
                                else:
                                        Rover.Forward(RotateSpeed)
                                        print "FORWARD"
        
            elif MachineState == "WayPoint":
               if Bump.getReading().value == 1:
                  ScreenLog.Log("Bumped into something")
                  Led.allOff()
                  Led.turnOn('teal')
                  # Time to avoid the obstacle by reversing, 
                  # turning right moving forward and turning back left again
                  AvoidObstacle()
               
               if WayPointData["nextWaypoint"] == 0:
                   ScreenLog.Log("Reached last way point.")
                   Led.allOff()
                   Led.turnOn('yellow')
                   Rover.Stop()
               else: 
                   if WayPointData["nextWaypoint"] != CurrentWayPoint: # If cone timer hasnt expired but we are done with the waypoints near a cone lets keep trying.
                       CurrentWayPoint = WayPointData["nextWaypoint"]
                       if (len(ConeWayPointBuffer) > 0) and (WayPointData["nextWaypointWeight"] == 0):
                           WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]-len(ConeWayPointBuffer)) 

                   elif (WayPointData["currentHorizontalAccuracy"]+2 < 2) and (WayPointData["distanceToNextWaypoint"] < (WayPointData["currentHorizontalAccuracy"]+2)):
                       ScreenLog.Log("Reached Waypoint: "+str(WayPointData["nextWaypoint"]))
                       Led.allOff()
                       Led.turnOn('green')
                       if WayPointData["nextWaypointWeight"] > 0:
                           Rover.Stop()
                           time.sleep(0.5)
                           ScreenLog.Log("Close to Cone, switching to Pixy Mode.")
                           MachineState = "PixyScan"
                           if len(ConeWayPointBuffer) == 0:
                               ConeTimer=0
                       else:
                           WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                           ConeWayPointBuffer = []
                   elif WayPointData["distanceToNextWaypoint"] <= 2: 
                       ScreenLog.Log("Reached Waypoint: "+str(WayPointData["nextWaypoint"]))
                       Led.allOff()
                       Led.turnOn('green')
                       if WayPointData["nextWaypointWeight"] > 0:
                           ScreenLog.Log("Close to Cone, switching to Pixy Mode.")
                           Rover.Stop()
                           time.sleep(0.5)
                           MachineState = "PixyScan"
                           if len(ConeWayPointBuffer) == 0:
                               ConeTimer=0
                       else:
                           WayPointSensor.setNextWaypoint(WayPointData["nextWaypoint"]+1)
                           ConeWayPointBuffer = []
                   else:
                       Led.allOff()
                       Led.turnOn('blue')
                       if WayPointData["currentHorizontalAccuracy"] < 5000:#20:
                           AngleDiff = WayPointData["headingToNextWaypoint"] - WayPointData["direction"]
                           if (AngleDiff < -180):
                               AngleDiff += 360
                           elif (AngleDiff > 180):
                               AngleDiff -= 360
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
            Rover.Stop()
            ScreenLog.Log("Kill Switch enabled.")
            Led.allOff()
            Led.turnOn('red')
    else:
        Rover.Stop()
        ScreenLog.Log("WayPoint data is None")                
        Led.allOff()
        Led.turnOn('red')

sys.exit(0)

