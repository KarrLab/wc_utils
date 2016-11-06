"""Test stochastic rounding utility.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import numpy as np
import unittest
from random import Random
from scipy.stats import binom

from wc_utils.util.rand import StochasticRound, ReproducibleRandom


class TestStochasticRound(unittest.TestCase):

    @staticmethod
    def get_sequence_of_rounds( samples, value, seed=None ):
        ReproducibleRandom.init( seed=seed )
        aStochasticRound = StochasticRound( ReproducibleRandom.get_numpy_random() )
        return [ aStochasticRound.stochastic_uniform_rounder( value ) for j in range(samples) ]

    def test_seed( self ):
        seed = 0
        samples = 100
        value = 3.5
        initial_results = TestStochasticRound.get_sequence_of_rounds( samples, value, seed=seed )
        test_results = TestStochasticRound.get_sequence_of_rounds( samples, value, seed=seed )
        self.assertEquals( initial_results, test_results )

        initial_results = TestStochasticRound.get_sequence_of_rounds( samples, value, seed=seed )
        test_results = TestStochasticRound.get_sequence_of_rounds( samples, value )
        # P[ this test failing | Random is truly random ] = 2**-100 = (2**-10)**10 ~= (10**-3)**10 = 10**-30
        self.assertNotEquals( initial_results, test_results )
        
    def test_mean( self ):
        # the mean of a set of values should converge towards the mean of stochastic rounds of the same set
        myRandom = Random()
        samples = 1000000
        lower, upper = (0,10)
        values = [myRandom.uniform( lower, upper ) for i in range(samples)]
        mean_values = sum(values)/float(samples)
        aStochasticRound = StochasticRound( )
        mean_stochastic_rounds_values = \
            sum( map( lambda x: aStochasticRound.stochastic_uniform_rounder( x ), values) )/float(samples)
        '''
        print( "samples: {:7d} mean_values: {:8.5f} mean_stochastic_rounds: {:8.5f}".format( 
            samples, mean_values, mean_stochastic_rounds_values ) )
        '''
        # TODO(Arthur): determine an analytic relationship between samples and places
        for i in range(10):
            self.assertAlmostEqual( mean_values, mean_stochastic_rounds_values, places=3 )        

    @unittest.skip("")
    def test_random_round(self):
        ReproducibleRandom.init()
        aStochasticRound = StochasticRound( rng=ReproducibleRandom.get_numpy_random() )
        
        self.assertEquals(aStochasticRound.random_round(3.4), 3)
        self.assertEquals(aStochasticRound.random_round(3.6), 4)
        samples = 1000
        obs_avg = np.mean([aStochasticRound.random_round(avg) for i in range(samples)])
        self.assertGreater(obs_avg, np.floor(avg) + binom.ppf(0.01, n=samples, p=avg % 1) / samples)
        self.assertLess(   obs_avg, np.floor(avg) + binom.ppf(0.99, n=samples, p=avg % 1) / samples)    
