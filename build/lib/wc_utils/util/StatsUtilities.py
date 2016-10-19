""" Statistical utilities.

:Author: Jonathan Karr, karr@mssm.edu
:Date: 3/22/2016
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 10/05/2016
:Copyright: 2016, Karr Lab
:License: MIT
"""

from random import Random
from numpy import random as numpy_random
import sys
import math
import numpy as np

class ExponentialMovingAverage(object):
    """An exponential moving average.
    
    Each moving average S is computed recursively from the sample values Y:
        S_1 = Y_1
        S_t = alpha * Y_t + (1-alpha)*S_(t-1)
    
    Attributes:
        alpha: float; the decay factor
    """
    def __init__( self, initial_value, alpha=None, center_of_mass=None ):
        """Initialize an ExponentialMovingAverage.
        
        Args:
            alpha: float; the decay factor
            center_of_mass: number; a center of mass for initializing alpha, the decay factor
                in an exponential moving average. alpha = 1/center_of_mass
        
        Raises:
            ValueError if alpha <= 0 or 1 <= alpha
        """
        if alpha != None:
            self.alpha = alpha
        elif center_of_mass != None:
            self.alpha = 1./(1.+center_of_mass)
        else:
            raise ValueError( "alpha or center_of_mass must be provided" )
        if self.alpha <= 0 or 1 <= self.alpha:
            raise ValueError( "alpha should satisfy 0<alpha<1: but alpha={}".format( self.alpha ) )
        self.exponential_moving_average = initial_value
        
    def add_value( self, value ):
        """Add a sample to this ExponentialMovingAverage, and get the next average.
        
        Args:
            value: number; the next value to contribute to the exponential moving average.
        
        Returns:
            The next exponential moving average.
        """
        self.exponential_moving_average = (self.alpha * value) \
            + (1-self.alpha)*self.exponential_moving_average
        return self.exponential_moving_average
    
    def get_value( self ):
        """Get the curent next average.
        
        Returns:
            The curent exponential moving average.
        """
        return self.exponential_moving_average
    

