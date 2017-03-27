""" Test introspection utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-03-27
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils.util.introspection import get_class_that_defined_function
import unittest


class A(object):

    def method0(self):
        pass

    def method1(self):
        pass


class B(A):

    def method0(self):
        super(B, self).method0()

    def method2(self):
        pass


class TestIntrospection(unittest.TestCase):

    def test_get_class_that_defined_function(self):
        self.assertEqual(get_class_that_defined_function(A.method0), A)
        self.assertEqual(get_class_that_defined_function(A.method1), A)
        self.assertEqual(get_class_that_defined_function(B.method0), B)
        self.assertEqual(get_class_that_defined_function(B.method1), A)
        self.assertEqual(get_class_that_defined_function(B.method2), B)
