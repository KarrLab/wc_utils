""" Util tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-20
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utils.util.types import TypesUtil, TypesUtilAssertionError
import numpy as np
import unittest


class TestCastToBuiltins(unittest.TestCase):

    def test_iterables(self):
        self.assertEqual(TypesUtil.cast_to_builtins([1, 2, 3]), [1, 2, 3])
        self.assertEqual(TypesUtil.cast_to_builtins((1, 2, 3)), [1, 2, 3])
        self.assertEqual(TypesUtil.cast_to_builtins(set([1, 2, 3])), [1, 2, 3])

    def test_dict(self):
        self.assertEqual(TypesUtil.cast_to_builtins({'x': 1}), {'x': 1})
        self.assertEqual(TypesUtil.cast_to_builtins(SetAttrClass(x=1)), {'x': 1})

    def test_scalars(self):
        self.assertEqual(TypesUtil.cast_to_builtins('test string'), 'test string')
        self.assertEqual(TypesUtil.cast_to_builtins(1), 1)
        self.assertEqual(TypesUtil.cast_to_builtins(2.0), 2.0)
        self.assertEqual(TypesUtil.cast_to_builtins(np.float64(2.0)), 2.0)
        self.assertEqual(TypesUtil.cast_to_builtins(np.float64(np.nan)).__class__, float('nan').__class__)

    def test_recursive(self):
        obj = SetAttrClass(
            a=(1, 2, 3),
            b=[4, 5, 6],
            c=[{'d': 7, 'e': 8}, SetAttrClass(f=9, g=10)],
        )
        expected = {
            'a': [1, 2, 3],
            'b': [4, 5, 6],
            'c': [{'d': 7, 'e': 8}, {'f': 9, 'g': 10}],
        }
        self.assertEqual(TypesUtil.cast_to_builtins(obj), expected)


class TestAssertValueEqual(unittest.TestCase):

    def test_type_not_equal(self):
        TypesUtil.assert_value_equal(1, 1.0)
        TypesUtil.assert_value_not_equal(1, 1.0, check_type=True)
        self.assertRaises(TypesUtilAssertionError, lambda: TypesUtil.assert_value_equal(1, 1.0, check_type=True))
        self.assertRaises(TypesUtilAssertionError, lambda: TypesUtil.assert_value_not_equal(1, 1.0))

        self.assertRaises(TypesUtilAssertionError, lambda: TypesUtil.assert_value_equal({'x': 1}, ['x', 1]))
        TypesUtil.assert_value_not_equal({'x': 1}, ['x', 1])

        self.assertRaises(TypesUtilAssertionError, lambda: TypesUtil.assert_value_equal(['x', 1], {'x': 1}))
        TypesUtil.assert_value_not_equal(['x', 1], {'x': 1})

    def test_iterables(self):
        TypesUtil.assert_value_equal([1, 3, 2], [1, 2, 3])
        TypesUtil.assert_value_equal([1, 3, 2, 1], [1, 1, 2, 3])
        TypesUtil.assert_value_equal((2, 3, 1), [1, 2, 3])
        TypesUtil.assert_value_equal(set([1, 2, 3]), [1, 2, 3])

        self.assertRaises(TypesUtilAssertionError, lambda: TypesUtil.assert_value_equal([1, 2, 3], [1, 1, 3]))
        TypesUtil.assert_value_not_equal([1, 2, 3], [1, 1, 3])

        self.assertRaises(TypesUtilAssertionError, lambda: TypesUtil.assert_value_equal([1, 2, 3], [1, 2]))
        TypesUtil.assert_value_not_equal([1, 2, 3], [1, 2])

    def test_dict(self):
        TypesUtil.assert_value_equal({'y': 2, 'x': 1}, {'x': 1, 'y': 2})
        TypesUtil.assert_value_equal(SetAttrClass(x=1, y=2), {'y': 2, 'x': 1})
        TypesUtil.assert_value_equal({'y': 2, 'x': 1}, SetAttrClass(x=1, y=2))

    def test_scalars(self):
        TypesUtil.assert_value_equal('test string', 'test string')
        TypesUtil.assert_value_equal(1, 1)
        TypesUtil.assert_value_equal(2.0, 2.0)
        TypesUtil.assert_value_equal(np.float64(2.0), 2.0)
        TypesUtil.assert_value_equal(float('nan'), np.nan)
        TypesUtil.assert_value_equal(float(2.0), np.float64(2.0))

    def test_recursive(self):
        obj = SetAttrClass(
            a=(1, 2, 3),
            b=[4, 5, 6],
            c=[SetAttrClass(f=9, g=[10, 'h', 11]), {'d': 7, 'e': 8}],
        )
        expected = {
            'a': [1, 2, 3],
            'b': [4, 5, 6],
            'c': [{'d': 7, 'e': 8}, {'f': 9, 'g': [10, 11, 'h']}],
        }
        TypesUtil.assert_value_equal(obj, expected)

    def test_is_iterable(self):
        self.assertTrue(TypesUtil.is_iterable( [] ))
        self.assertTrue(TypesUtil.is_iterable( () ))
        self.assertFalse(TypesUtil.is_iterable( {} ))
        self.assertFalse(TypesUtil.is_iterable( '' ))
        self.assertFalse(TypesUtil.is_iterable( None ))
        self.assertFalse(TypesUtil.is_iterable( int() ))
        self.assertFalse(TypesUtil.is_iterable( float() ))


class TestAssertValueNotEqual(unittest.TestCase):

    def test_scalars(self):
        TypesUtil.assert_value_not_equal(1, np.nan)
        TypesUtil.assert_value_not_equal(1, 2)


class SetAttrClass(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
