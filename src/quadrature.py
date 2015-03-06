#!/usr/bin/env python

### Class to read encoders while in motion ###

import encoder

class quadrature():
    def __init__(self):
        self.right_encoder = encoder.EncoderController(port="/dev/ttyO1", UART="UART1")
        self.left_encoder = encoder.EncoderController(port="/dev/ttyO2", UART="UART2")
        return

    def getDistance(self):
        distance_right = self.right_encoder.getDistance()
        distance_left = self.left_encoder.getDistance()
        return {'distance_right':distance_right, 'distance_left':distance_left}


    def getVelocity(self):
        velocity_right = self.right_encoder.getVelocity()
        velocity_left = self.left_encoder.getVelocity()
        return {'velocity_right':velocity_right, 'velocity_left':velocity_left}

    def move(self, distance_to_travel):
        start_distance = self.getDistance()
        while ((self.right_encoder.getDistance()['distance_right']-start_distance['distance_right']) and (self.getDistance['distance_left']-start_distance['distance_left'])) < distance_to_travel:
            pass
        else:
            return True
