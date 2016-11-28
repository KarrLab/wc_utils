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
import unittest, math, sys

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

    def test_all_stochastic_rounds(self):
        random_state = RandomState()
        x = 3.5

        for method in ['binomial', 'midpoint', 'poisson', 'quadratic']:
            round = random_state.round( x, method=method)
            self.assertEqual( round, int(round))
            if method in ['binomial', 'midpoint', 'quadratic']:
                self.assertIn( round, [math.floor(x), math.ceil(x)] )

        with self.assertRaises(Exception) as context:
            random_state.round( 3.5, 'no_such_method')
        self.assertIn( 'Undefined rounding method', str(context.exception) )

    def test_round_binomial(self):
        random_state = RandomState()
        x = 3
        self.assertEqual( random_state.round_binomial(x), x)

        avg = 3.4
        samples = 50000

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
        samples = 3000
        obs_avg = np.mean([random_state.round_midpoint(avg) for i in range(samples)])
        min = np.floor(avg) + binom.ppf(0.01, n=samples, p=avg % 1) / samples
        max = np.floor(avg) + binom.ppf(0.99, n=samples, p=avg % 1) / samples
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_poisson(self):
        random_state = RandomState()
        avg = 3.4
        samples = 10000

        rounds = [random_state.round_poisson(avg) for i in range(samples)]
        obs_avg = np.mean(rounds)
        min = poisson.ppf(0.01, mu=avg)
        max = poisson.ppf(0.99, mu=avg)
        self.assertGreater(obs_avg, min)
        self.assertLess(obs_avg, max)

    def test_round_quadratic(self):
        random_state = RandomState()
        nsamples=50000

        # test limits
        for avg in [3.25, 3.75]:
            rounds = [random_state.round_quadratic(avg) for i in range(nsamples)]
            for r in rounds:
                self.assertLessEqual(r, np.ceil(avg))
                self.assertLessEqual(np.floor(avg), r)
            obs_avg = np.mean(rounds)

        # test skew
        for i in range(10):
            lesser,greater = sorted(np.random.random_sample(2))
            lesser_rounds = [random_state.round_quadratic(lesser) for i in range(nsamples)]
            ave_lesser_rounds = np.mean(lesser_rounds)
            greater_rounds = [random_state.round_quadratic(greater) for i in range(nsamples)]
            ave_greater_rounds = np.mean(greater_rounds)
            self.assertLessEqual(ave_lesser_rounds, ave_greater_rounds)

        # test mean
        samples = list(np.random.random_sample(nsamples))
        obs_avg = np.mean([random_state.round_quadratic(s) for s in samples])
        print(obs_avg)
        self.assertLess(abs(obs_avg - 0.5), 0.1)

    @unittest.skip("plot distributions of the stochastic rounding methods in wc_utils.util.rand")
    @unittest.skipIf(sys.version_info.major==2, 'does not work on python 2')
    def test_plot_rounding(self):
        random_state = RandomState()
        import matplotlib.pyplot as plt

        n_intervals = 100
        n_samples = 10000
        for method in ['binomial', 'midpoint', 'poisson', 'quadratic']:
            x = sorted([x/n_intervals for x in range(n_intervals+1)]*n_samples)
            rounds = [random_state.round( value, method=method) for value in x]
            results = list(zip(x,rounds))
            down = [x for x,r in results if r==0]
            up = [x for x,r in results if r==1]
            labels = [ "{}: {}".format(method,r) for r in ['down','up']]
            plt.hist([down, up], bins=n_intervals+1, histtype='step', label=labels, normed=True, )
            legend = plt.legend(loc='upper right', )
            plt.show()

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
