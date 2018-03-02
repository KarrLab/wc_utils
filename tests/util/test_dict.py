""" Test dict util

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-08-25
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from wc_utils.util.dict import DictUtil
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

    def test_dict_filtering(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(DictUtil.filtered_dict(d, []), {})
        self.assertEqual(DictUtil.filtered_dict(d, ['a']), {'a': 1})
        self.assertEqual(DictUtil.filtered_dict(d, ['a', 'd', 'a', 'b', 'c']), d)

        self.assertEqual({(k, v) for k, v in DictUtil.filtered_iteritems(d, ['a', 'b', 'd'])},
                         {('a', 1), ('b', 2)})

    def test_to_string_sorted_by_key(self):
        self.assertEqual(DictUtil.to_string_sorted_by_key(None), '{}')
        self.assertEqual(DictUtil.to_string_sorted_by_key({'b': 2, 'c': 3, 'a': 1, 'd': 4}), "{'a': 1, 'b': 2, 'c': 3, 'd': 4}")

    def test_set_value(self):
        key = 'key'
        key_a_dict_value = 8
        key_b_dict_value = 3
        key_c_dict_value = 'hi'
        test_dict = {
        'a_dict':
            {'nested': {'key': key_a_dict_value,
                       'not_key': 9}},
        'b_dict':
            {'nested': {'key': key_b_dict_value,
                    'not_key': 15}},
        'c_dict':
            {'key': {'key': key_c_dict_value,
                    'not_key': 15}}
                    }
        self.assertEqual(test_dict['a_dict']['nested'][key], key_a_dict_value)
        self.assertEqual(test_dict['b_dict']['nested'][key], key_b_dict_value)
        self.assertEqual(test_dict['c_dict']['key'][key], key_c_dict_value)

        new_value = 11
        DictUtil.set_value(test_dict, key, new_value)
        self.assertEqual(test_dict['a_dict']['nested'][key], new_value)
        self.assertEqual(test_dict['b_dict']['nested'][key], new_value)
        self.assertEqual(test_dict['c_dict']['key'][key], key_c_dict_value)

        DictUtil.set_value(test_dict, key, new_value, match_type=False)
        self.assertEqual(test_dict['a_dict']['nested'][key], new_value)
        self.assertEqual(test_dict['b_dict']['nested'][key], new_value)
        self.assertEqual(test_dict['c_dict']['key'][key], new_value)
