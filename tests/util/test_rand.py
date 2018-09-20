""" Random utility tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-03
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from copy import deepcopy
from matplotlib import pyplot
from numpy import random
from scipy.stats import binom, poisson
from wc_utils.util.rand import RandomState, RandomStateManager, validate_random_state, InvalidRandomStateException
import numpy as np
import unittest
import math
import sys


class TestRandomState(unittest.TestCase):

    def test_round(self):
        random_state = RandomState()
        avg = 3.4
        samples = 1000

        obs_avg = np.mean([random_state.round(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.001, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.999, n=samples, p=avg % 1) / samples
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_all_stochastic_rounds(self):
        random_state = RandomState()
        x = 3.5

        for method in ['binomial', 'midpoint', 'poisson', 'quadratic']:
            round = random_state.round(x, method=method)
            self.assertEqual(round, int(round))
            if method in ['binomial', 'midpoint', 'quadratic']:
                self.assertIn(round, [math.floor(x), math.ceil(x)])

        with self.assertRaises(Exception) as context:
            random_state.round(3.5, 'no_such_method')
        self.assertIn('Undefined rounding method', str(context.exception))

    def test_round_binomial(self):
        random_state = RandomState()
        x = 3
        self.assertEqual(random_state.round_binomial(x), x)

        avg = 3.4
        samples = 1000

        obs_avg = np.mean([random_state.round_binomial(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.001, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.999, n=samples, p=avg % 1) / samples
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_midpoint(self):
        random_state = RandomState()

        self.assertEqual(random_state.round_midpoint(3.4), 3)
        self.assertEqual(random_state.round_midpoint(3.6), 4)

        avg = 3.5
        samples = 2000
        obs_avg = np.mean([random_state.round_midpoint(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.0001, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.9999, n=samples, p=avg % 1) / samples
        self.assertGreaterEqual(obs_avg, min)
        self.assertLessEqual(obs_avg, max)

    def test_round_poisson(self):
        random_state = RandomState()
        avg = 3.4
        samples = 1000

        rounds = [random_state.round_poisson(avg) for i in range(samples)]
        obs_avg = np.mean(rounds)
        min = poisson.ppf(0.001, mu=avg)
        max = poisson.ppf(0.999, mu=avg)
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_quadratic(self):
        random_state = RandomState()
        nsamples = 50000

        # test limits
        for avg in [3.25, 3.75]:
            rounds = [random_state.round_quadratic(avg) for i in range(nsamples)]
            for r in rounds:
                self.assertLessEqual(r, np.ceil(avg))
                self.assertLessEqual(np.floor(avg), r)
            obs_avg = np.mean(rounds)

        # test skew
        for i in range(10):
            lesser, greater = (0.2, 0.8)
            lesser_rounds = [random_state.round_quadratic(lesser) for i in range(nsamples)]
            ave_lesser_rounds = np.mean(lesser_rounds)
            greater_rounds = [random_state.round_quadratic(greater) for i in range(nsamples)]
            ave_greater_rounds = np.mean(greater_rounds)
            self.assertLessEqual(ave_lesser_rounds, ave_greater_rounds)

        # test mean
        samples = list(np.random.random_sample(nsamples))
        obs_avg = np.mean([random_state.round_quadratic(s) for s in samples])
        self.assertLess(abs(obs_avg - 0.5), 0.1)

    def test_ltd(self):
        random_state = RandomState()
        self.assertGreaterEqual(random_state.ltd(), 0.)
        self.assertLessEqual(random_state.ltd(), 1.)

    def test_rtd(self):
        random_state = RandomState()
        self.assertGreaterEqual(random_state.rtd(), 0.)
        self.assertLessEqual(random_state.rtd(), 1.)

    def test_plot_rounding(self):
        random_state = RandomState()
        n_intervals = 100
        n_samples = 10000
        for method in ['binomial', 'midpoint', 'poisson', 'quadratic']:
            x = sorted([x/n_intervals for x in range(n_intervals+1)]*n_samples)
            rounds = [random_state.round(value, method=method) for value in x]
            results = list(zip(x, rounds))
            down = [x for x, r in results if r == 0]
            up = [x for x, r in results if r == 1]
            labels = ["{}: {}".format(method, r) for r in ['down', 'up']]
            pyplot.hist([down, up], bins=n_intervals+1, histtype='step', label=labels, density=True, )
            legend = pyplot.legend(loc='upper right', )
            # pyplot.show()
            pyplot.close()


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

        with self.assertRaisesRegex(InvalidRandomStateException, '^Random state must be a tuple$'):
            validate_random_state(1.)

        with self.assertRaisesRegex(InvalidRandomStateException, '^Random state must have length 5$'):
            validate_random_state((1,))

        with self.assertRaisesRegex(InvalidRandomStateException, r'^Random number generator random_state\[1\] must be an array of length 624 of unsigned ints$'):
            validate_random_state(('MT19937', [1.] * 624, 1, 1, 1))
