#!/usr/bin/env python

import Adafruit_BBIO.UART as UART
import serial
import struct

UART.setup("UART4")

encoderCom = serial.Serial(port = "/dev/ttyO4", baudrate=38400)
encoderCom.close()
encoderCom.open()

if encoderCom.isOpen():
    print "Serial open!"
    while True:
        line = encoderCom.readline().strip()
        if line.startswith("D"):
            value = line[1:]
            value = struct.unpack('!i', value.decode('hex'))[0]
            print "Distance: {}".format(value)
        elif line.startswith("V"):
            value = int(line[1:], 16)
            print "Velocity: {}".format(value)
        else:
            pass

encoderCom.close()
