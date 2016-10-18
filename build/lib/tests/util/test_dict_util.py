""" Test dict util

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-25
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utilities.util.dict import DictUtil
from copy import deepcopy
import unittest


class DictUtilTest(unittest.TestCase):

    def test_nested_in(self):
        dict = {
            'a': {
                'b': {
                    'c': 1,
                    'd': 2,
                },
            },
            'e': {
                'f': 3,
                'g': 4,
            },
        }

        self.assertEqual(DictUtil.nested_in(dict, 'a.b'), 'a' in dict and 'b' in dict['a'])
        self.assertEqual(DictUtil.nested_in(dict, 'a.b.c'), 'a' in dict and 'b' in dict['a'] and 'c' in dict['a']['b'])
        self.assertEqual(DictUtil.nested_in(dict, 'a.b.e'), 'a' in dict and 'b' in dict['a'] and 'e' in dict['a']['b'])

    def test_nested_get(self):
        dict = {
            'a': {
                'b': {
                    'c': 1,
                    'd': 2,
                },
            },
            'e': {
                'f': 3,
                'g': 4,
            },
        }

        self.assertEqual(DictUtil.nested_get(dict, 'a.b'), dict['a']['b'])
        self.assertEqual(DictUtil.nested_get(dict, 'a.b.c'), dict['a']['b']['c'])
        self.assertEqual(DictUtil.nested_get(dict, 'e'), dict['e'])
        self.assertEqual(DictUtil.nested_get(dict, 'e.g'), dict['e']['g'])

    def test_nested_set(self):
        dict = {
            'a': {
                'b': {
                    'c': 1,
                    'd': 2,
                },
            },
            'e': {
                'f': 3,
                'g': 4,
            },
        }

        new_val = 3
        expected = deepcopy(dict)
        expected['a']['b'] = new_val
        self.assertEqual(DictUtil.nested_set(deepcopy(dict), 'a.b', new_val), expected)

        new_val = 10
        expected = deepcopy(dict)
        expected['a']['b']['c'] = new_val
        self.assertEqual(DictUtil.nested_set(deepcopy(dict), 'a.b.c', new_val), expected)

        new_val = {'x': {'y': 'z'}}
        expected = deepcopy(dict)
        expected['e'] = new_val
        self.assertEqual(DictUtil.nested_set(deepcopy(dict), 'e', new_val), expected)

        new_val = [-1, 0, 1]
        expected = deepcopy(dict)
        expected['e']['g'] = new_val
        self.assertEqual(DictUtil.nested_set(deepcopy(dict), 'e.g', new_val), expected)
