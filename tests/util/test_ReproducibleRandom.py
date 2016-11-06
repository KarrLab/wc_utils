""" Installation utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import unittest
import re

from wc_utils.util.rand import ReproducibleRandom as RepRand

class TestRepRand(unittest.TestCase):

    def setUp(self):
        pass
        
    @staticmethod
    def get_samples(n):
        rs = RepRand.get_numpy_random_state()
        rv=[]
        for i in range(n):
            rv.append( rs.random_sample() )
        return rv

    def test_ReproducibleRandom(self):
        samples=[]
        n=10
        for turn in 'first second'.split():
            RepRand.init( reproducible=True )
            if turn == 'first':
                samples = TestRepRand.get_samples(n)
            elif turn == 'second':
                self.assertEqual( samples, TestRepRand.get_samples(n) ) 
            
    @staticmethod
    def use_seed(s,n):
        RepRand.init( seed=s )
        nprand = RepRand.get_numpy_random()
        [nprand.tomaxint() for i in range(n)]

    def test_ReproducibleRandom2(self):
        self.assertEqual( TestRepRand.use_seed(17,3), TestRepRand.use_seed(17,3) ) 
