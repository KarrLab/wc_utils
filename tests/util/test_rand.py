""" Random utility tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from numpy import random
from scipy.stats import binom, poisson
from wc_utils.util.rand import RandomState, RandomStateManager, validate_random_state, InvalidRandomStateException
import numpy as np
import unittest


class TestRandomState(unittest.TestCase):

    def test_round(self):
        random_state = RandomState()
        avg = 3.4
        samples = 10000

        obs_avg = np.mean([random_state.round(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.01, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.99, n=samples, p=avg % 1) / samples
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_binomial(self):
        random_state = RandomState()
        avg = 3.4
        samples = 10000

        obs_avg = np.mean([random_state.round_binomial(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.01, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.99, n=samples, p=avg % 1) / samples
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_midpoint(self):
        random_state = RandomState()

        self.assertEquals(random_state.round_midpoint(3.4), 3)
        self.assertEquals(random_state.round_midpoint(3.6), 4)

        avg = 3.5
        samples = 1000
        obs_avg = np.mean([random_state.round_midpoint(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.01, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.99, n=samples, p=avg % 1) / samples
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_poisson(self):
        random_state = RandomState()
        avg = 3.4
        samples = 10000

        obs_avg = np.mean([random_state.round_poisson(avg) for i in range(samples)])
        min = poisson.ppf(0.01, mu=avg)
        max = poisson.ppf(0.99, mu=avg)
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)


class TestRandomStateManager(unittest.TestCase):

    def test_singleton(self):
        r1 = RandomStateManager.instance()
        r2 = RandomStateManager.instance()
        self.assertEqual(r1, r2)

        r1.seed(123)
        r2.seed(456)
        np.testing.assert_equal(r1.get_state(), r2.get_state())
        self.assertEqual(r1, r2)


class TestValidateRandomState(unittest.TestCase):

    def test_validate_random_state(self):
        r1 = random.get_state()
        self.assertTrue(validate_random_state(r1))

        r2 = list(r1)
        self.assertTrue(validate_random_state(r2))

        r3 = deepcopy(r2)
        r3[0] = 'xxx'
        self.assertRaises(InvalidRandomStateException, validate_random_state, r3)

        r3 = deepcopy(r2)
        r3[1] = [1]
        self.assertRaises(InvalidRandomStateException, validate_random_state, r3)

        r3 = deepcopy(r2)
        r3[2] = 1.2
        self.assertRaises(InvalidRandomStateException, validate_random_state, r3)

        r3 = deepcopy(r2)
        r3[3] = 1.2
        self.assertRaises(InvalidRandomStateException, validate_random_state, r3)

        r3 = deepcopy(r2)
        r3[4] = 'x'
        self.assertRaises(InvalidRandomStateException, validate_random_state, r3)
