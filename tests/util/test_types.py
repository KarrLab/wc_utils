""" Util tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-20
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from wc_utils.util.types import assert_value_equal, assert_value_not_equal, cast_to_builtins, is_iterable, get_subclasses, get_superclasses, TypesUtilAssertionError
import numpy as np
import unittest


class TestCastToBuiltins(unittest.TestCase):

    def test_iterables(self):
        self.assertEqual(cast_to_builtins([1, 2, 3]), [1, 2, 3])
        self.assertEqual(cast_to_builtins((1, 2, 3)), [1, 2, 3])
        self.assertEqual(cast_to_builtins(set([1, 2, 3])), [1, 2, 3])

    def test_dict(self):
        self.assertEqual(cast_to_builtins({'x': 1}), {'x': 1})
        self.assertEqual(cast_to_builtins(SetAttrClass(x=1)), {'x': 1})

    def test_scalars(self):
        self.assertEqual(cast_to_builtins('test string'), 'test string')
        self.assertEqual(cast_to_builtins(1), 1)
        self.assertEqual(cast_to_builtins(2.0), 2.0)
        self.assertEqual(cast_to_builtins(np.float64(2.0)), 2.0)
        self.assertEqual(cast_to_builtins(np.float64(np.nan)).__class__, float('nan').__class__)

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
        self.assertEqual(cast_to_builtins(obj), expected)


class TestAssertValueEqual(unittest.TestCase):

    def test_type_not_equal(self):
        assert_value_equal(1, 1.0)
        assert_value_not_equal(1, 1.0, check_type=True)
        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_equal(1, 1.0, check_type=True))
        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_not_equal(1, 1.0))

        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_equal({'x': 1}, ['x', 1]))
        assert_value_not_equal({'x': 1}, ['x', 1])

        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_equal(['x', 1], {'x': 1}))
        assert_value_not_equal(['x', 1], {'x': 1})

    def test_iterables(self):
        assert_value_equal([1, 3, 2], [1, 2, 3])
        assert_value_equal([1, 3, 2, 1], [1, 1, 2, 3])
        assert_value_equal((2, 3, 1), [1, 2, 3])
        assert_value_equal(set([1, 2, 3]), [1, 2, 3])

        assert_value_equal([1, 2, 3], [1, 2, 3], check_iterable_ordering=True)
        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_equal([1, 2, 3], [1, 3, 2], check_iterable_ordering=True))

        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_equal([1, 2, 3], [1, 1, 3]))
        assert_value_not_equal([1, 2, 3], [1, 1, 3])

        self.assertRaises(TypesUtilAssertionError, lambda: assert_value_equal([1, 2, 3], [1, 2]))
        assert_value_not_equal([1, 2, 3], [1, 2])

    def test_dict(self):
        assert_value_equal({'y': 2, 'x': 1}, {'x': 1, 'y': 2})
        assert_value_equal(SetAttrClass(x=1, y=2), {'y': 2, 'x': 1})
        assert_value_equal({'y': 2, 'x': 1}, SetAttrClass(x=1, y=2))

    def test_scalars(self):
        assert_value_equal('test string', 'test string')
        assert_value_equal(1, 1)
        assert_value_equal(2.0, 2.0)
        assert_value_equal(np.float64(2.0), 2.0)
        assert_value_equal(float('nan'), np.nan)
        assert_value_equal(float(2.0), np.float64(2.0))

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
        assert_value_equal(obj, expected)

    def test_is_iterable(self):
        self.assertTrue(is_iterable([]))
        self.assertTrue(is_iterable(()))
        self.assertFalse(is_iterable({}))
        self.assertFalse(is_iterable(''))
        self.assertFalse(is_iterable(None))
        self.assertFalse(is_iterable(int()))
        self.assertFalse(is_iterable(float()))


class TestAssertValueNotEqual(unittest.TestCase):

    def test_scalars(self):
        assert_value_not_equal(1, np.nan)
        assert_value_not_equal(1, 2)


class TestGetSubclasses(unittest.TestCase):

    def test(self):
        self.assertEqual(get_subclasses(Parent1), set([Child11, Child12]))
        self.assertEqual(get_subclasses(GrandParent), set([Parent1, Parent2, Child11, Child12, Child21, Child22]))
        self.assertEqual(get_subclasses(GrandParent, immediate_only=True), set([Parent1, Parent2]))


class TestGetSuperclasses(unittest.TestCase):

    def test(self):
        self.assertEqual(get_superclasses(GrandParent), (object, ))
        self.assertEqual(get_superclasses(Parent1), (GrandParent, object, ))
        self.assertEqual(get_superclasses(Child11, immediate_only=True), (Parent1, ))
        self.assertEqual(get_superclasses(Child11), (Parent1, GrandParent, object, ))


class SetAttrClass(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class GrandParent(object):
    pass


class Parent1(GrandParent):
    pass


class Parent2(GrandParent):
    pass


class Child11(Parent1):
    pass


class Child12(Parent1):
    pass


class Child21(Parent2):
    pass


class Child22(Parent2):
    pass
