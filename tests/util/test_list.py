""" Test list utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-30
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utils.util.list import is_sorted, transpose, difference
import unittest


class TestTranspose(unittest.TestCase):

    def test_is_sorted(self):
        self.assertTrue(is_sorted([1, 2, 3]))
        self.assertFalse(is_sorted([2, 1, 3]))

        self.assertTrue(is_sorted(['a', 'b', 'c']))
        self.assertFalse(is_sorted(['c', 'b', 'a']))

        self.assertTrue(is_sorted([1, 2, 3], le_cmp=lambda x, y: x <= y))
        self.assertFalse(is_sorted([2, 1, 3], le_cmp=lambda x, y: x <= y))

    def test_transpose(self):
        lst = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        t_lst = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
        self.assertEqual(transpose(lst), t_lst)

    def test_difference(self):
        l = list([0, 1, 2, 3, 4])
        m = list([1, 2, 3])
        self.assertEqual(difference(l, m), [0, 4])
        self.assertEqual(difference(m, l), [])
        with self.assertRaises(TypeError):
            self.assertEqual(difference([], [[1]]), [])
