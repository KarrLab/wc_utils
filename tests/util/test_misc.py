""" Test misc

:Author: Arthur Goldberg, Arthur.Goldberg@mssm.edu
:Date: 2016-12-10
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
import unittest
import numpy as np
import os
import pickle
import shutil
import tempfile

from wc_utils.util.misc import (most_qual_cls_name, round_direct, OrderableNone, quote, isclass,
                                isclass_by_name, obj_to_str, as_dict, internet_connected,
                                geometric_iterator, DFSMAcceptor, EnhancedDataClass)
from wc_utils.util.stats import ExponentialMovingAverage


class C(object):

    class D(object):
        pass
d = C.D()


class TestMisc(unittest.TestCase):

    def setUp(self):
        class A(object):
            ATTRIBUTES = ['a1', 'a2']
            def __init__(self, a1):
                self.a1 = a1
                self.a2 = 3
        self.A = A

    def test_isclass(self):
        class str2(object):
            pass

        class int2(object):
            pass

        self.assertTrue(isclass(str2, str2))
        self.assertTrue(isclass(str2, (str2, )))

        self.assertFalse(isclass(str2, int2))
        self.assertFalse(isclass(str2, (int2, )))

        self.assertTrue(isclass(str2, (int2, str2, )))

    def test_isclass_by_name(self):
        str2 = type('str2', (object, ), {})
        self.assertTrue(isclass_by_name('tests.util.test_misc.str2', str2))

        class str3(object):
            pass
        name3 = 'tests.util.test_misc.TestMisc.test_isclass_by_name.<locals>.str3'
        self.assertTrue(isclass_by_name(name3, str3))

        class str4():
            pass
        str5 = type('str5', (), {})
        name4 = 'tests.util.test_misc.TestMisc.test_isclass_by_name.<locals>.str4'
        self.assertTrue(isclass_by_name(name4, (((str4, ), ), str5)))
        self.assertFalse(isclass_by_name(name3, (((str4, ), ), str5)))

    def test_get_qual_name(self):

        ema = ExponentialMovingAverage(1, .5)
        self.assertEqual(most_qual_cls_name(self), 'tests.util.test_misc.TestMisc')
        self.assertEqual(most_qual_cls_name(TestMisc), 'tests.util.test_misc.TestMisc')
        self.assertEqual(most_qual_cls_name(ema),
                         'wc_utils.util.stats.ExponentialMovingAverage')
        self.assertEqual(most_qual_cls_name(ExponentialMovingAverage),
                         'wc_utils.util.stats.ExponentialMovingAverage')

        try:
            # Fully qualified class names are available for Python >= 3.3.
            hasattr(self, '__qualname__')
            self.assertEqual(most_qual_cls_name(d), 'tests.util.test_misc.C.D')
        except:
            self.assertEqual(most_qual_cls_name(d), 'tests.util.test_misc.D')

    def test_round_direct(self):
        self.assertEqual(round_direct(3.01, 2), '3.01')
        self.assertEqual(round_direct(3.01), '3.01')
        self.assertEqual(round_direct(3.011), '3.01+')
        self.assertEqual(round_direct(3.01, 1), '3.0+')
        self.assertEqual(round_direct(2.99, 1), '3.0-')

    def test_orderable_none(self):
        self.assertTrue(OrderableNone < 1)
        self.assertTrue(OrderableNone <= 1)
        self.assertFalse(OrderableNone == 1)
        self.assertFalse(OrderableNone >= 1)
        self.assertFalse(OrderableNone > 1)

        self.assertFalse(1 < OrderableNone)
        self.assertFalse(1 <= OrderableNone)
        self.assertFalse(1 == OrderableNone)
        self.assertTrue(1 >= OrderableNone)
        self.assertTrue(1 > OrderableNone)

        self.assertFalse(OrderableNone < None)
        self.assertTrue(OrderableNone <= None)
        self.assertTrue(OrderableNone == None)
        self.assertTrue(OrderableNone >= None)
        self.assertFalse(OrderableNone > None)

        self.assertFalse(None < OrderableNone)
        self.assertTrue(None <= OrderableNone)
        self.assertTrue(None == OrderableNone)
        self.assertTrue(None >= OrderableNone)
        self.assertFalse(None > OrderableNone)

        self.assertFalse(OrderableNone < OrderableNone)
        self.assertTrue(OrderableNone <= OrderableNone)
        self.assertTrue(OrderableNone == OrderableNone)
        self.assertTrue(OrderableNone >= OrderableNone)
        self.assertFalse(OrderableNone > OrderableNone)

        self.assertFalse(OrderableNone < OrderableNone)
        self.assertTrue(OrderableNone <= OrderableNone)
        self.assertTrue(OrderableNone == OrderableNone)
        self.assertTrue(OrderableNone >= OrderableNone)
        self.assertFalse(OrderableNone > OrderableNone)

        x = [1, 3, 2, OrderableNone]
        y = sorted(x)
        self.assertEqual(y[0], OrderableNone)
        self.assertEqual(y[1], 1)
        self.assertEqual(y[2], 2)
        self.assertEqual(y[3], 3)

        x = [OrderableNone, 1, 3, 2]
        y = sorted(x)
        self.assertEqual(y[0], OrderableNone)
        self.assertEqual(y[1], 1)
        self.assertEqual(y[2], 2)
        self.assertEqual(y[3], 3)

        x = [3, 1, OrderableNone, 2]
        y = sorted(x)
        self.assertEqual(y[0], OrderableNone)
        self.assertEqual(y[1], 1)
        self.assertEqual(y[2], 2)
        self.assertEqual(y[3], 3)

    def test_quote(self):
        self.assertEqual(quote('x'), "x")
        self.assertEqual(quote('x y'), "'x y'")

    def test_obj_to_str(self):
        a = self.A('test_a1')
        str_rep = obj_to_str(a, ['a2', 'a1'])
        self.assertIn('Class: A', str_rep)
        self.assertIn('a1: test_a1', str_rep)
        self.assertIn('a2: 3', str_rep)
        self.assertIn('not defined', obj_to_str(a, ['x']))

    def test_as_dict(self):
        A = self.A
        a = A('test_a1')
        self.assertEqual(as_dict(a), {'a1': 'test_a1', 'a2': 3})
        class B(object):
            ATTRIBUTES = ['b1', 'b2']
            def __init__(self):
                self.b1 = A('from B')
                self.b2 = [6]
        b = B()
        self.assertEqual(as_dict(b), {'b1': {'a1': 'from B', 'a2': 3}, 'b2': [6]})

        class C(object):    pass
        c = C()
        with self.assertRaises(ValueError) as context:
            as_dict(c)

    def test_internet_connected(self):
        self.assertEqual(internet_connected(), internet_connected())

    def test_geometric_iterator(self):
        self.assertEqual([2, 4, 8], list(geometric_iterator(2, 10, 2)))
        self.assertEqual([1e-05, 0.0001, 0.001, 0.01, 0.1], list(geometric_iterator(1E-5, 0.1, 10)))
        np.testing.assert_allclose([.1, .3], list(geometric_iterator(0.1, 0.3, 3)))
        with self.assertRaisesRegexp(ValueError, '0 < min is required'):
            next(geometric_iterator(-1, 0.3, 3))
        with self.assertRaisesRegexp(ValueError, '0 < min is required'):
            next(geometric_iterator(0, 0.3, 3))
        with self.assertRaisesRegexp(ValueError, 'min <= max is required'):
            next(geometric_iterator(1, 0.3, 3))
        with self.assertRaisesRegexp(ValueError, '1 < factor is required'):
            next(geometric_iterator(.1, 0.3, .6))


class TestDFSMAcceptor(unittest.TestCase):

    def test_dfsm_acceptor(self):
        transitions_for_two_repititions_exercise = [     # (state, message, new state)
            ('start', 'do exercise', 'done 1'),
            ('done 1', 'do exercise', 'done 2'),
        ]
        dfsm_acceptor = DFSMAcceptor('start', 'done 2', transitions_for_two_repititions_exercise)
        dfsm_acceptor.reset()
        self.assertEqual(None, dfsm_acceptor.exec_transition('do exercise'))
        self.assertEqual('done 1', dfsm_acceptor.get_state())
        self.assertEqual(DFSMAcceptor.ACCEPT, dfsm_acceptor.run(['do exercise', 'do exercise']))
        self.assertEqual(DFSMAcceptor.FAIL, dfsm_acceptor.run(['do exercise']))
        self.assertEqual(DFSMAcceptor.FAIL, dfsm_acceptor.run([7, 'do exercise']))

        with self.assertRaisesRegex(ValueError, 'already a transition from'):
            DFSMAcceptor('s', 'e', [('s', 'm', 0), ('s', 'm', 'e')])

        with self.assertRaisesRegex(ValueError, 'no transitions available from start state'):
            DFSMAcceptor('s', 'e', [('f', 'm1', 0), ('e', 'm1', 'f')])


@dataclass
class InnerClassFiltersPickle(EnhancedDataClass):
    DO_NOT_PICKLE = {'bad'}
    bad: object = None


@dataclass
class  OuterClassFiltersPickle(EnhancedDataClass):
    DO_NOT_PICKLE = {'j'}
    i: int
    f: float = None
    o: InnerClassFiltersPickle = None

    @staticmethod
    def get_pathname(dirname):
        return os.path.join(dirname, 'outer_class_filters_pickle.pickle')


@dataclass
class InnerClassDoesNotFilterPickle(EnhancedDataClass):
    i: int
    s: str = None


@dataclass
class OuterClassDoesNotFilterPickle(EnhancedDataClass):
    j: int
    o: InnerClassDoesNotFilterPickle
    f: float = 1.0

    @staticmethod
    def get_pathname(dirname):
        return os.path.join(dirname, 'outer_class_does_not_filter_pickle.pickle')


@dataclass
class TestClassNoGetPathname(EnhancedDataClass):
    m: int


@dataclass
class TestClassOverwrite(EnhancedDataClass):
    m: int

    @staticmethod
    def get_pathname(dirname):
        return os.path.join(dirname, 'test_class_overwrite.pickle')


class TestEnhancedDataClass(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_validate_dataclass_type(self):

        o = InnerClassDoesNotFilterPickle(1, 'x')
        self.assertEquals(o.validate_dataclass_type('i'), None)
        self.assertEquals(o.validate_dataclass_type('s'), None)
        o = InnerClassDoesNotFilterPickle(2)
        self.assertEquals(o.validate_dataclass_type('i'), None)

        # test accept int inputs to float fields
        f = 4
        o = OuterClassFiltersPickle(i=3, f=f)
        self.assertEquals(o.validate_dataclass_type('f'), None)
        self.assertEquals(o.f, float(f))

        # test 'an' int, no default
        with self.assertRaisesRegex(TypeError, "an int"):
            InnerClassDoesNotFilterPickle(1.3)

        # test default
        with self.assertRaisesRegex(TypeError, "a str"):
            InnerClassDoesNotFilterPickle(1, 1.4)

        # test bad name
        o = InnerClassDoesNotFilterPickle(2)
        with self.assertRaises(ValueError):
            o.validate_dataclass_type('bad name')

    def test_validate_dataclass_types(self):

        o = InnerClassDoesNotFilterPickle(1, 'hi')
        self.assertEquals(o.validate_dataclass_types(), None)

    inner_class_filters_pickle = InnerClassFiltersPickle(bad=object())
    outer_class_filters_pickle = OuterClassFiltersPickle(i=3, o=inner_class_filters_pickle)
    inner_class_does_not_filter_pickle = InnerClassDoesNotFilterPickle(3, 'ab')
    outer_class_does_not_filter_pickle = OuterClassDoesNotFilterPickle(7, inner_class_does_not_filter_pickle)

    def test_write_and_read(self):
        OuterClassDoesNotFilterPickle.write_dataclass(self.outer_class_does_not_filter_pickle, self.tmp_dir)
        self.assertEqual(OuterClassDoesNotFilterPickle.read_dataclass(self.tmp_dir),
                         self.outer_class_does_not_filter_pickle)

        with self.assertRaisesRegexp(ValueError,
                                     'subclasses of EnhancedDataClass .* must define get_pathname method'):
            TestClassNoGetPathname.get_pathname(self.tmp_dir)

        test_class_overwrite = TestClassOverwrite(1)
        TestClassOverwrite.write_dataclass(test_class_overwrite, self.tmp_dir)
        with self.assertRaisesRegexp(ValueError, '.* already exists'):
            TestClassOverwrite.write_dataclass(test_class_overwrite, self.tmp_dir)

    def round_trip_pickle_test(self, validated_dataclass):
        """ Round-trip test of pickle write and read of EnhancedDataClass """
        file = os.path.join(self.tmp_dir, 'test.pickle')
        prepared_to_pickle = validated_dataclass.prepare_to_pickle()
        with open(file, 'wb') as fd:
            pickle.dump(prepared_to_pickle, fd)
        with open(file, 'rb') as fd:
            loaded_validated_dataclass = pickle.load(fd)
        self.assertEquals(prepared_to_pickle, loaded_validated_dataclass)

    def test_prepare_to_pickle(self):
        # test test_cls.prepare_to_pickle() == test_cls.prepare_to_pickle().prepare_to_pickle() for any test_cls
        for instance in [self.inner_class_filters_pickle,
                         self.outer_class_filters_pickle,
                         self.inner_class_does_not_filter_pickle,
                         self.outer_class_does_not_filter_pickle]:
            self.assertEquals(instance.validate_dataclass_types(), None)
            self.assertEquals(instance.prepare_to_pickle(), instance.prepare_to_pickle().prepare_to_pickle())

        for outer_instance in [self.outer_class_filters_pickle, self.outer_class_does_not_filter_pickle]:
            self.round_trip_pickle_test(outer_instance)

        # test that filtered attribute is not set
        prepared_to_pickle = self.inner_class_filters_pickle.prepare_to_pickle()
        self.assertEquals(prepared_to_pickle.bad, None)
