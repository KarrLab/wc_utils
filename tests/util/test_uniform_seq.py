""" Test uniform sequence

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2019-12-11
:Copyright: 2019, Karr Lab
:License: MIT
"""

from decimal import Decimal
import unittest
import sys

from wc_utils.config.core import get_config
from wc_utils.util.uniform_seq import UniformSequence
UNIFORM_SEQ_PRECISION = get_config()['wc_utils']['misc']['uniform_seq_precision']


class TestUniformSequence(unittest.TestCase):

    def test_uniform_sequence(self):
        initial_and_expected_values = \
            [((0, 1), (0, 1, 2, 3)),
              ((2, 1), (2, 3)),
              ((0, -1), (0, -1, -2, -3)),
              # non integer values are loaded as strings so that Decimal represents them exactly
              ((0, '.1'), (0, '.1', '.2', '.3')),
              ((0, '.100'), (0, '.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8', '.9', 1)),
              ((0, '-.100'), (0, '-0.1', '-0.2', '-0.3', '-0.4')),
              ((0, '.3'), (0, '.3', '.6', '.9', '1.2')),
              # example from Guido van Rossum: http://code.activestate.com/recipes/577068/
              ((0, '.7'), (0, '.7', '1.4', '2.1')),
        ]
        for args, expected_seq in initial_and_expected_values:
            start, period = args
            us = UniformSequence(start, period)
            for expected in expected_seq:
                next = us.__next__()
                self.assertEqual(next, Decimal(expected))
        for args, expected_seq in initial_and_expected_values:
            start, period = args
            us = UniformSequence(start, period)
            for expected in expected_seq:
                self.assertEqual(us.next_float(), float(expected))

        us = UniformSequence(0, 1)
        self.assertEqual(us.__iter__(), us)

        bad_steps = [0, float('nan'), float('inf'), -float('inf')]
        for bad_step in bad_steps:
            with self.assertRaisesRegex(ValueError, "UniformSequence: step=.* can't be 0, NaN, "
                                                    "infinite, or subnormal"):
                UniformSequence(0, bad_step)

        with self.assertRaisesRegex(ValueError, "precision in start=.* exceeds UNIFORM_SEQ_PRECISION threshold"):
            UniformSequence(1/3, 1)

        nonterminating_steps = [2**0.5, 1/3]
        for nonterminating_step in nonterminating_steps:
            with self.assertRaisesRegex(ValueError, "precision in step=.* exceeds UNIFORM_SEQ_PRECISION threshold"):
                UniformSequence(0, nonterminating_step)

        with self.assertRaisesRegex(ValueError, "precision in step=.* exceeds UNIFORM_SEQ_PRECISION threshold"):
            UniformSequence(0, '0.123456789')

    def test_truncate(self):
        not_too_much_precision = float('1.' + '1' * UNIFORM_SEQ_PRECISION)
        self.assertEqual(UniformSequence.truncate(not_too_much_precision), str(not_too_much_precision))
        with self.assertRaisesRegex(StopIteration, 'UniformSequence: truncation error:'):
            too_much_precision = float('1.' + '1' * (UNIFORM_SEQ_PRECISION + 1))
            UniformSequence.truncate(too_much_precision)
