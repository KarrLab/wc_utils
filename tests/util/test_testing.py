""" Tests of the testing utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2019-06-18
:Copyright: 2019, Karr Lab
:License: MIT
"""

from wc_utils.util import testing
import unittest


class TestingTestCase(unittest.TestCase):
    def test_memory(self):
        testing.assert_memory_less(1, 100)
        with self.assertRaisesRegex(ValueError, 'memory is greater than or equal to '):
            testing.assert_memory_less(1000 * [1], 100, exclusive=True)

        testing.assert_memory_less_equal(1, 100)
        with self.assertRaisesRegex(ValueError, 'memory is greater than '):
            testing.assert_memory_less_equal(1000 * [1], 100, exclusive=True)
