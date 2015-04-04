#!/usr/bin/env python


#
#
#  Pure Big Mad Boat Men sample sensor implementation, v0.7
#
#

## required
import atexit
import collections
import datetime
import os
import Queue
import serial
import signal
import sys
import syslog
import threading
import time




#### util

## quit gracefully, kill all threads
gThreadMap = {}
def ctrlCHandler(signal, frame):
  print "  CTRL-C HANDLER CALLED"
  for k,v in gThreadMap.items():
    try:
      v.quit()
    except:
      pass
  os._exit(0)

signal.signal(signal.SIGINT, ctrlCHandler)


## syslog
syslog.openlog('RobotMaria', os.getpid(), syslog.LOG_DAEMON)

def logDebug(inMsg):
  syslog.syslog(syslog.LOG_DEBUG, "DEBUG " + str(inMsg))

def logInfo(inMsg):
  syslog.syslog(syslog.LOG_INFO, "INFO " + str(inMsg))

def logErr(inMsg):
  syslog.syslog(syslog.LOG_ERR, "ERROR " + str(inMsg))

##
def ForceDtor(cls):
  """ class decorator to force __del__ call at process exit
  """
  def getinstance(*a, **b):
    inst = cls(*a, **b)
    atexit.register(inst.__del__)
    return inst
  return getinstance


#### caveman state machine
class StateMachine(object):
  def __init__(self):
    self.handlers_ = {}
    self.startState_ = None
    self.endStates_ = []

  def add_state(self, name, handler, end_state=0):
    name = name.lower()
    self.handlers_[name] = handler
    if end_state:
      self.endStates_.append(name)

  def set_start(self, name):
    self.startState_ = name.lower()

  def run(self, cargo):
    try:
       handler = self.handlers_[self.startState_]
    except:
      raise Exception("InitializationError", "must call .set_start() before .run()")
    if not self.endStates_:
      raise Exception("InitializationError", "at least one state must be an end_state")
    while 1:
      (newState, cargo) = handler(cargo)
      if newState.lower() in self.endStates_:
        break 
      else:
        handler = self.handlers_[newState.lower()]


#### global state of all sensors
##       may not be necessary in this example
@ForceDtor
class SensorState(object):
  def __init__(self):
    try:
      self.sensorMap_ = {}
      self.sensorInputQueue_ = Queue.PriorityQueue()
      self.quitEvent_ = threading.Event()
      self.queueThread_ = threading.Thread(target=self.__queueThreadProc)
      self.queueThread_.daemon = True
    except Exception, err:
      errStr = "[ERROR] setting up SensorState %s\n" % (err)
      sys.stderr.write(errStr)
      raise "InitializationError", errStr

  def __del__(self):
    for sensor in self.sensorMap_.values(): 
      try:
        sensor.sleepEvent.clear()
        sensor.quitEvent.set()
      except:
        pass
    self.quitEvent_.set()

  def start(self):
    self.queueThread_.start()

  def quit(self):
    self.__del__()

  def registerSensor(self, inSensorObj, inDoStart=True):
    self.sensorMap_[inSensorObj.name_] = {'value':None, 'updatedDatetime':datetime.datetime.now(), 
                                     'quitEvent':inSensorObj.quitEvent_, 'sleepEvent':inSensorObj.sleepEvent_}
    if inDoStart:
      inSensorObj.start(self.sensorInputQueue_)
    else:
      inSensorObj.outputQueue_ = self.sensorInputQueue_

  def getReading(self, inSensorName):
    try:
      return collections.namedtuple("out", "value, updatedDatetime")\
                                           (self.sensorMap_[inSensorName]['value'], 
                                            self.sensorMap_[inSensorName]['updatedDatetime'])
    except:
      return collections.namedtuple("out", "value, updatedDatetime")\
                                           (None,  None) 

  def postReading(self, inSensorName, inSensorValue, inUpdatedDatetime, inPriority):
    if inSensorName in self.sensorMap_:
      self.sensorInputQueue_.put((inPriority, inSensorName, inSensorValue, inUpdatedDatetime))

  def dump(self):
    print "\t\tFOUND", len(self.sensorMap_), "SENSORS" 
    for k,v in self.sensorMap_.items(): 
      print "\t\t\t", k, "=", v['value'], "  UPDATED:", v['updatedDatetime']

  def __queueThreadProc(self):
    while not self.quitEvent_.isSet():
      try:
        priority, sensorName, sensorValue, updatedDatetime = self.sensorInputQueue_.get(True, 0.05)
        self.sensorMap_[sensorName]['value'] = sensorValue
        self.sensorMap_[sensorName]['updatedDatetime'] = updatedDatetime
        self.sensorInputQueue_.task_done()
        print "\t\tGRIM SENSOR THREAD GOT AN UPDATE FOR", sensorName, "=", sensorValue
      except Queue.Empty:
        continue
      except Exception, err:
        errStr = "[ERROR] bad sensor event queued %s\n" % (err)
        sys.stderr.write(errStr)

  def queueFlush(self):
    while 1:
      try:
        self.sensorInputQueue_.get(True, 0.05)
        self.sensorInputQueue_.task_done()
      except Queue.Empty:
        break

  def reset(self, inSensorName=None):
    for sensorName in self.sensorMap_.keys(): 
      if (None == inSensorName) or (sensorName == inSensorName):
        self.sensorMap_[sensorName]['value'] = None






#### a sensor
class Sensor(object):
  def __init__(self, inName, inSensorThreadProc, inSensorThreadProcKWArgs={}, inDefaultPriority=3):
    global gThreadMap
    try:
      self.name_ = inName
      self.defaultPriority_ = inDefaultPriority
      self.sensorThread_ = threading.Thread(target=inSensorThreadProc, 
                                            kwargs=inSensorThreadProcKWArgs)
      self.sensorThread_.daemon = True
      self.defaultPriority_ = inDefaultPriority
      self.currentValue_ = None
      self.updatedDatetime_ = None
      self.outputQueue_ = None
      self.quitEvent_ = threading.Event()
      self.sleepEvent_ = threading.Event()
      if inName in gThreadMap:
        errStr = "[ERROR] sensor name %s already exists\n" % (self.name_)
        logErr(errStr)
        raise Exception("InitializationError " + errStr)
      gThreadMap[inName] = self

    except Exception, err:
      errStr = "[ERROR] setting up sensor %s  %s\n" % (inName, err)
      logErr(errStr)
      raise Exception("InitializationError " + errStr)

  def __del__(self):
    self.quit()

  def start(self, inOuputQueue=None):
    self.outputQueue_ = inOuputQueue
    self.sensorThread_.start()

  def quit(self):
    try:
      self.sleepEvent_.clear()
    except:
      pass
    try:
      self.quitEvent_.set()
    except:
      pass
    print "THREAD QUIT COMPLETE", self.name_

  def sleep(self):
    self.sleepEvent_.set()

  def wake(self):
    self.sleepEvent_.clear()

  def getReading(self):
    return collections.namedtuple("out", "value, updatedDatetime")\
                                           (self.currentValue_, 
                                            self.updatedDatetime_)

  def postReading(self, inSensorValue, inPriority=None):
    self.updatedDatetime_ = datetime.datetime.now()
    self.currentValue_ = inSensorValue
    if None == inPriority:
      inPriority = self.defaultPriority_
    if None == self.outputQueue_:
      pass
#      errStr = "[ERROR] %s sensor start() not called\n" % (self.name_)
#      logErr(errStr)
#      raise Exception("StartError " + errStr)
    else:
      self.outputQueue_.put((inPriority, self.name_, self.currentValue_, self.updatedDatetime_))


    





#### example sensors

class FakeWaypointSensor(Sensor):
  def __init__(self, inName, inDefaultPriority=3, **kwargs):
    # boilerplate bookkeeping
    Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc, 
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=2)
 
  # service the sensor, post the value 
  def __threadProc(self, **kwargs):
    while not self.quitEvent_.isSet():                     # should we quit?
      sensorReadMap = {
        "nextWaypoint": 0,
        "killSwitch": 0,
        "direction": 180,                   
        "distanceToNextWaypoint": 200,       
        "headingToNextWaypoint": 181,        
        "currentHorizontalAccuracy": 50,    
        "nextWaypointWeight": 0.3         
      }

#      sys.stdout.write('\a')   # annoy

      print "\tFakeWaypointSensor %s SPEAKS: %s" % (self.name_, str(sensorReadMap))
      self.postReading(sensorReadMap, 2)                   # "medium" priority
      time.sleep(1)
      while self.sleepEvent_.isSet():
        time.sleep(0.5)



class WaypointSensor(Sensor):
  kSampleIntervalSecs = 0.2
  kExpectedReadSize = 22
#  kSerialPortName = "/dev/tty.usbserial-A603RM49"
  kSerialPortName = "/dev/ttyUSB0"
  kSerialBaudRate = 38400
  kWriteTimeout = 1
  kRobotStateTextMaxSize = 20

  def __init__(self, inName, inDefaultPriority=2, **kwargs):
    Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc, 
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=inDefaultPriority)
    self.nextWaypointNum_ = 2
    self.robotStateText_ = (" " * self.kRobotStateTextMaxSize)
    self.sensorReadMap_ = {
        "nextWaypoint": 0,                    # ex: 2
        "killSwitch": 0,                      # ex: 0 boolean
        "direction": 0,                       # ex: 180 degrees (south)
        "distanceToNextWaypoint": 0,          # ex: 200 meters
        "headingToNextWaypoint": 0,           # ex: 90 degrees (east)
        "currentHorizontalAccuracy": 0,       # ex: 10 meters
        "nextWaypointWeight": 0.0             # ex: 0.9 cone value
    }
    self.serialPortName_ = self.kSerialPortName
    if None == self.openSerialPort():
      raise Exception("InitializationError")
    self.writeQueue_ = Queue.PriorityQueue()
    self.queueThread_ = threading.Thread(target=self.__queueThreadProc)
    self.queueThread_.daemon = True


  def openSerialPort(self):
    for i in xrange(10):
      try:
        self.serialPort_ = serial.Serial(self.serialPortName_, self.kSerialBaudRate, writeTimeout=self.kWriteTimeout)
        return self.serialPort_
      except Exception, err:
        errStr = "[ERROR] opening serial port %s \t%s\n" % (self.serialPortName_, err)
        logErr(errStr)
        time.sleep(1)
    return None


  def start(self):
    Sensor.start(self)
    self.queueThread_.start()
    

  def __threadProc(self, **kwargs):
    self.setRobotStateText("START")
    while not self.quitEvent_.isSet():
      if 0 == self.sensorReadMap_["nextWaypoint"]:
        self.setRobotStateText("FINISH")
      try:
        try:
          self.serialPort_.flushInput()
        except:
          pass
        response = self.serialPort_.readline()
        nextWaypoint = int(response[:3])
        if self.kExpectedReadSize == len(response):
          self.sensorReadMap_["killSwitch"] = int(response[3:4])
          self.sensorReadMap_["direction"] = int(response[4:7])
          self.sensorReadMap_["currentHorizontalAccuracy"] = int(response[14:18])
          if nextWaypoint == self.nextWaypointNum_:
            self.sensorReadMap_["nextWaypoint"] = nextWaypoint
            self.sensorReadMap_["distanceToNextWaypoint"] = int(response[7:11])
            self.sensorReadMap_["headingToNextWaypoint"] = int(response[11:14])
            self.sensorReadMap_["nextWaypointWeight"] = float(response[18:])
          elif 0 == nextWaypoint:
            self.sensorReadMap_["nextWaypoint"] = 0
            self.sensorReadMap_["distanceToNextWaypoint"] = 0
            self.sensorReadMap_["headingToNextWaypoint"] = 0
            self.sensorReadMap_["nextWaypointWeight"] = 0
            logInfo("Received waypoint == 0, course complete")
            time.sleep(10)
          else:
            continue
        else:
          continue
      except ValueError, err:
        continue
      except Exception, err:
        errStr = "[ERROR] reading from serial port %s \t%s\n" % (self.serialPortName_, err)
        logErr(errStr)
        try:
          self.serialPort_.close()
        except:
          pass
        time.sleep(0.5)
        self.openSerialPort()
        continue
      print "WaypointSensor %s SPEAKS: %s" % (self.name_, str(self.sensorReadMap_))
#      logErr("-->WaypointSensor %s SPEAKS: %s" % (self.name_, str(self.sensorReadMap_)))
      self.postReading(self.sensorReadMap_)             
      time.sleep(self.kSampleIntervalSecs)
      if self.sleepEvent_.isSet():
        try:
          self.serialPort_.close()
        except:
          pass 
        while self.sleepEvent_.isSet():
          time.sleep(0.5)
        self.openSerialPort()
    # after quit
    try:
      self.serialPort_.close()
    except:
      pass


  def __queueThreadProc(self):
    while not self.quitEvent_.isSet():
      try:
        priority, writeStr = self.writeQueue_.get(True, 0.05)
        self.writeQueue_.task_done()
        self.__write(writeStr + '\0')
      except Queue.Empty:
        continue
      except Exception, err:
        errStr = "[ERROR] bad serial write event queued %s\n" % (err)
        sys.stderr.write(errStr)
      time.sleep(0.2)


  def write(self, inWriteStr, inPriority=2):
      self.writeQueue_.put((inPriority, inWriteStr))


  def __write(self, inWriteStr):
    while 1:
      try:
        print ("NOW WRITING LEN %d |" % (len(inWriteStr))) + inWriteStr + "|"
        numBytesWritten = self.serialPort_.write(inWriteStr + "\0")
        if numBytesWritten == (len(inWriteStr)+1):
          break
      except Exception, err:
        errStr = "[ERROR] writing to serial port %s \t%s\n" % (self.serialPortName_, err)
        logErr(errStr)
        try:
          self.serialPort_.close()
        except:
          pass
        time.sleep(0.5)
        self.openSerialPort()
        continue
  

  # waypoints are numbered starting with 1, next waypoint is always >= 2
  def setNextWaypoint(self, inNextWaypointNum):
    if (inNextWaypointNum < 2) or (inNextWaypointNum > 999):
      errStr = "[ERROR] attempt to set bad waypoint number %s" % (str(inNextWaypointNum))
      logErr(errStr)
      return      
    self.nextWaypointNum_ = int(inNextWaypointNum)
    writeStr = "%03d" % (self.nextWaypointNum_)
    while 1:
      self.write(writeStr, 1)
      time.sleep(0.3)
      try:
        if self.getReading().value["nextWaypoint"] == self.nextWaypointNum_:
          break
        elif 0 == self.getReading().value["nextWaypoint"]:
          self.nextWaypointNum_ = 0
          break
      except:
        time.sleep(0.2)


  def setRobotStateText(self, inRobotStateText):
    self.robotStateText_ = (inRobotStateText + (" " * self.kRobotStateTextMaxSize))[:self.kRobotStateTextMaxSize]
    writeStr = "%03d" % (self.nextWaypointNum_)
    writeStr += (self.robotStateText_)
    self.write(writeStr)


  def logToScreen(self, inLogText):
    writeStr = "%03d" % (self.nextWaypointNum_)
    writeStr += (self.robotStateText_)
    writeStr += (inLogText)
    self.write(writeStr)



#### example main thread

if  "__main__" == __name__: 

  ## add a sensor
  waypointSensor = WaypointSensor("WaypointSensor")
  waypointSensor.start()

  waypointSensor.setNextWaypoint(2)
#  waypointSensor.setRobotStateText("from sensor")
#  waypointSensor.logToScreen("some NEW log text")
  time.sleep(5)
  

  ## do something in main thread "loop"
  while 1:

    for i in xrange(5):
      print "MAIN", i
      time.sleep(1)
      print "waypointSensor value:", waypointSensor.getReading()  


      waypointSensor.setNextWaypoint(i)
      waypointSensor.setRobotStateText("state %d" % (i))
      waypointSensor.logToScreen("some NEW log text %d" % (i))


