import Adafruit_BBIO.ADC as ADC #Similar to analog read
import time as T
import math as m
#
# For the BeagleBone Black the input voltage has to be 0-1.8V
# The easiest way is with a voltage divider
#
#              Ra             Rb
# Vin -->--[== 1K ==]--+--[== 470 ==]----+
#                      |                 |
#                      V                 |
#                      |                 |
#                     Vout              === Gnd
#                                        -
#           Rb
# Vout = --------- x Vin
#         Ra + Rb
#
# scale factor for voltage divider to get original Vin: (Ra+Rb)/Rb
class IRSensor(object):

    def __init__(self, AIN="AIN1", min=10, max=80, scale=2.5,const=1, coeff=28, power=-1):
        self.AIN = AIN
        self.min = min
        self.max = max
        self.scale = scale
        self.coeff = coeff
        self.power = power
        ADC.setup(AIN)
        return



	def IRdistance():
		# Useful Lists:
		IR1list = []
# 		IR2list = []
# 		IR3list = []
# 		IR4list = []
# 		IR5list = []

		# General purpose variables:
		count = 0
		samples = 20
		voltMulti = 5

		ADC.setup()

		# Reading analog inputs:
		IR1 = ADC.read("P9_33") * voltMulti #added a voltage multiplier
# 		IR2 = ADC.read("P9_35") * voltMulti
# 		IR3 = ADC.read("P9_36") * voltMulti
# 		IR4 = ADC.read("P9_39") * voltMulti
# 		IR5 = ADC.read("P9_37") * voltMulti

		for i in range(samples):
			count = count + 1

			IR1list.append(IR1)
# 			IR2list.append(IR2)
# 			IR3list.append(IR3)
# 			IR4list.append(IR4)
# 			IR5list.append(IR5)

			if (count == samples):
				# Calculating the average of 20 readings:
				avgIR1 = round(sum(IR1list) / len(IR1list),3)
# 				avgIR2 = round(sum(IR2list) / len(IR2list),3)
# 				avgIR3 = round(sum(IR3list) / len(IR3list),3)
# 				avgIR4 = round(sum(IR4list) / len(IR4list),3)
# 				avgIR5 = round(sum(IR5list) / len(IR5list),3)
			
				# Clearing each list:
				IR1list = []
# 				IR2list = []
# 				IR3list = []
# 				IR4list = []
# 				IR5list = []
				count = 0

#		return (avgIR1, avgIR2, avgIR3, avgIR4, avgIR5)
		return (41.543 * m.pow((avgIR1 + 0.30221), -1.5281))


# 	def distanceCalc(volt):
# 		# NOTE: This function works only if you position the sensor 10cm from the edge.
# 		return (41.543 * m.pow((volt + 0.30221), -1.5281))


if __name__ == '__main__':
#we first initialize the class; then read the voltage and finally convert the voltage to a distance.  
 
    IR = IRSensor("P9_36", scale=1470.0/470.0, min=10, max=50, const=1, coeff=26.686363, power=-1.162602)
    while 1:
    	distance = IR.IRdistance()
        print distance
        sleep(1)
        
        	
