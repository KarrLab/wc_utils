""" Enumeration tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-12-09
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from wc_utils.util.enumerate import CaseInsensitiveEnum
from unittest import TestCase


class EnumTest(CaseInsensitiveEnum):
    AbC = 1
    GhI = 2


class EnumTestCase(TestCase):

    def test_new(self):
        self.assertEqual(set(EnumTest.__members__.keys()), set(('abc', 'ghi')))

    def test_getattr(self):
        self.assertEqual(EnumTest.ABC, EnumTest.abc)
        self.assertEqual(EnumTest.AbC, EnumTest.abc)

    def test_getitem(self):
        self.assertEqual(EnumTest['ghi'], EnumTest.ghi)
        self.assertEqual(EnumTest['GhI'], EnumTest.ghi)
        self.assertEqual(EnumTest['GHI'], EnumTest.ghi)
