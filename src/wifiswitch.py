import os
import time
import sensorState

class WifiSwitch(sensorState.Sensor):
    def __init__(self, inName, inDefaultPriority=3, host_ip = "172.20.10.1", timeout = 2, **kwargs):
        sensorState.Sensor.__init__(self, inName, inSensorThreadProc=self.__threadProc,
                            inSensorThreadProcKWArgs=kwargs, inDefaultPriority=3)
        self.WifiStatus = False
        self.HostIP = host_ip
        self.Timeout = timeout
        return

    def CheckWifi(self):
        ping = os.system("ping -i .1 -c 1 -W 50 "+str(self.HostIP)+" > /dev/null")
        if ping == 0:
            self.WifiStatus = True
        else:
            self.WifiStatus = False
    
    def __threadProc(self, **kwargs):
        while not self.quitEvent_.isSet():                      # should we quit?
            self.CheckWifi()
            self.postReading(self.WifiStatus, 1)
            time.sleep(self.Timeout)

            while self.sleepEvent_.isSet():                      # should we sleep?
                time.sleep(1)

