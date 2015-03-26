#!/usr/bin/env python


#
#
#  Pure Big Mad Boat Men sample sensor implementation, v0.1
#
#

## required
import atexit
import collections
import datetime
import Queue
import threading
import time

## for example only
import random



#### util
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
      raise "InitializationError", "must call .set_start() before .run()"
    if not self.endStates_:
      raise "InitializationError", "at least one state must be an end_state"
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
    except Exception, err:
      errStr = "[ERROR] setting up sensor %s  %s\n" % (inName, err)
      sys.stderr.write(errStr)
      raise "InitializationError", errStr

  def __del__(self):
    self.quit()

  def start(self, inOuputQueue):
    self.outputQueue_ = inOuputQueue
    self.sensorThread_.start()

  def quit(self):
    try:
      self.sleepEvent_.clear()
      self.quitEvent_.set()
    except:
      pass

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
      errStr = "[ERROR] %s sensor start() not called\n" % (self.name_)
#      sys.stderr.write(errStr)
#      raise "StartError", errStr
    else:
      self.outputQueue_.put((inPriority, self.name_, self.currentValue_, self.updatedDatetime_))







#### example sensors

class ZarkonSensor(Sensor):
  def __init__(self, inName, inDefaultPriority=3, **kwargs):
    # boilerplate bookkeeping
    Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc, 
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=3)

    self.initialVal_ = 1                                   # ZarkonSensor-specific member data
      
  # service the sensor, post the value 
  def __threadProc(self, **kwargs):
    myReading = self.initialVal_
    while not self.quitEvent_.isSet():                     # should we quit?
      # generate some scalar ODD INTEGER sensor readings
      myReading += kwargs["incrementBy"]                   # ZarkonSensor takes one parameter, incrementBy
      print "\tZARKON %s SPEAKS: %s" % (self.name_, str(myReading))
      self.postReading(myReading, 1)                       # "high" priority
      time.sleep(1)
      while self.sleepEvent_.isSet():                      # should we sleep?
        time.sleep(0.5)



class FweepSensor(Sensor):
  def __init__(self, inName, inDefaultPriority=3, **kwargs):
    Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc, 
                    inSensorThreadProcKWArgs=kwargs, inDefaultPriority=3)
    
    self.sum_ = 0                                          # fweep sensors need averaging
    self.numSamples_ = 0

  def __threadProc(self, **kwargs):
    myReading = [0, 2.0]
    while not self.quitEvent_.isSet():
      # generate some vector (list) EVEN FLOAT sensor readings
      myReading[0] += 2.0
      myReading[1] = random.random()
      self.sum_ += myReading[1]
      self.numSamples_ += 1
      print "\tFWEEP %s SPEAKS: %s" % (self.name_, str(myReading))
      self.postReading(myReading)
      time.sleep(1.9)
      while self.sleepEvent_.isSet():
        time.sleep(0.5)

  def average(self):                                       # some additional functionality needed for fweeps
    try:
      return float(self.sum_) / self.numSamples_
    except:
      return float('NaN')





#### example main thread

if  "__main__" == __name__: 

  ## state of all of our sensors
  sensorState = SensorState()
  sensorState.start()

  ## add a sensor
  zarkonSensor1 = ZarkonSensor("zarkon1", incrementBy=2)
  sensorState.registerSensor(zarkonSensor1)

  ## add another sensor of the same type
  zarkonSensor2 = ZarkonSensor("zarkon2", incrementBy=42)
  sensorState.registerSensor(zarkonSensor2)

  ## add another sensor of a different type
  fweepSensor = FweepSensor("fweep1")
  sensorState.registerSensor(fweepSensor)

  ## do something in main thread "loop"
  while 1:

    for i in xrange(3):
      print "MAIN", i
      time.sleep(5)
      print "zarkon1 value:", sensorState.getReading("zarkon1")   # get individual sensor value from global sensors state
  
    fweepSensor.sleep()                # put one sensor to sleep

    print ("=" * 50), "fweep sleeps"
    for i in xrange(3):
      print "MAIN", i
      time.sleep(5)
      print "zarkon1 value:", zarkonSensor1.getReading()          # get individual sensor value from sensor

    fweepSensor.wake()                 # wake it up

    print ("=" * 50), "fweep wakes"
    for i in xrange(3):
      print "MAIN", i
      time.sleep(5)
      sensorState.dump()                                          # get all sensor values from global sensors state
      print "FWEEP AVERAGE:", fweepSensor.average()

    ## clear all sensor values
    sensorState.reset()

