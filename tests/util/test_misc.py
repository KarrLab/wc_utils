'''Test misc

:Author: Arthur Goldberg, Arthur.Goldberg@mssm.edu
:Date: 2016-12-10
:Copyright: 2016-2018, Karr Lab
:License: MIT
'''

import six
import unittest
from wc_utils.util.misc import most_qual_cls_name, round_direct, OrderableNone, quote, isclass, isclass_by_name
from wc_utils.util.stats import ExponentialMovingAverage


class C(object):

    class D(object):
        pass
d = C.D()


class TestMisc(unittest.TestCase):

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
        if six.PY3:
            name3 = 'tests.util.test_misc.TestMisc.test_isclass_by_name.<locals>.str3'
        else:
            name3 = 'tests.util.test_misc.str3'
        self.assertTrue(isclass_by_name(name3, str3))

        class str4():
            pass
        str5 = type('str5', (), {})
        if six.PY3:
            name4 = 'tests.util.test_misc.TestMisc.test_isclass_by_name.<locals>.str4'
        else:
            name4 = 'tests.util.test_misc.str4'
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
