""" Random utility tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from numpy import random
from wc_utils.util.rand_utils import validate_random_state, InvalidRandomStateException
import unittest


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
