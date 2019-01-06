""" Test list utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-30
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import unittest
from wc_utils.util.list import (is_sorted, transpose, difference, det_dedupe, det_find_dupes,
    elements_to_str, det_count_elements, dict_by_class)


class TestListUtilities(unittest.TestCase):

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
        l = [0, 1, 2, 3, 4]
        m = [1, 2, 3]
        self.assertEqual(difference(l, m), [0, 4])
        self.assertEqual(difference(m, l), [])
        with self.assertRaises(TypeError):
            self.assertEqual(difference([], [[1]]), [])

    def test_det_dedupe(self):
        l = [0, 1, 2, 0, 1, 0, 7, 1]
        expected = [0, 1, 2, 7]
        self.assertEqual(det_dedupe(l), expected)
        self.assertEqual(det_dedupe([]), [])
        with self.assertRaises(TypeError):
            det_dedupe([[]])

    def test_det_find_dupes(self):
        l = [0, 1, 2, 0, 1, 7, 1]
        expected = [0, 1]
        self.assertEqual(det_find_dupes(l), expected)
        self.assertEqual(det_find_dupes([]), [])
        with self.assertRaises(TypeError):
            det_find_dupes([[]])

    def test_det_count_elements(self):
        l = 'a b c b b c'.split()
        expected = [('a', 1), ('b', 3), ('c', 2)]
        self.assertEqual(det_count_elements(l), expected)
        self.assertEqual(det_count_elements([]), [])
        with self.assertRaises(TypeError):
            det_count_elements([[]])

    def test_elements_to_str(self):
        l = 'a b c'.split()
        self.assertEqual(elements_to_str(l), l)
        l = [1, 'x']
        self.assertEqual(elements_to_str(l), ['1', 'x'])

    def test_dict_by_class(self):
        self.assertEqual(dict_by_class([]), {})
        self.assertEqual(dict_by_class([1, 3, 'hi', 'mom']), {int: [1, 3], str: ['hi', 'mom']})
