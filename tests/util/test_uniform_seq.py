""" Test uniform sequence

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2019-12-11
:Copyright: 2019, Karr Lab
:License: MIT
"""

from math import pi
import unittest
import sys

from wc_utils.util.uniform_seq import UniformSequence


class TestUniformSequence(unittest.TestCase):

    def test_uniform_sequence(self):
        initial_values = [((0, 1), (0, 1, 2, 3)),
                          ((2, 1), (2, 3)),
                          ((0, -1), (0, -1, -2, -3)),
                          ((0, .1), (0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.)),
                          ((0, .3), (0, .3, .6, .9, 1.2)),
                          # an example from Guido van Rossum: http://code.activestate.com/recipes/577068/
                          ((0, .7), (0, .7, 1.4, 2.1)),
                         ]
        for args, expected_seq in initial_values:
            start, period = args
            us = UniformSequence(start, period)
            for expected in expected_seq:
                next = us.__next__()
                self.assertEqual(next, expected)
                self.assertEqual(float(us.truncate(next)), next)

        us = UniformSequence(0, 1)
        self.assertEqual(us.__iter__(), us)

        with self.assertRaisesRegex(ValueError, "UniformSequence: step .* can't be a fraction"):
            UniformSequence(0, pi)

        us = UniformSequence(sys.float_info.max, 2)
        with self.assertRaisesRegex(StopIteration, "UniformSequence: floating-point rounding error:"):
            us.__next__()
            us.__next__()

        us = UniformSequence(pi, 1)
        with self.assertRaisesRegex(StopIteration, "UniformSequence: truncation error"):
            us.truncate(us.__next__())
