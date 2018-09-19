""" Tests of the chemistry utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_utils.util import chem
import unittest


class TestChem(unittest.TestCase):

    def test_EmpiricalFormula_constructor(self):
        f = chem.EmpiricalFormula()
        self.assertEqual(f, {})

        f = chem.EmpiricalFormula('H')
        self.assertEqual(f, {'H': 1})

        f = chem.EmpiricalFormula('H2')
        self.assertEqual(f, {'H': 2})

        f = chem.EmpiricalFormula('He2')
        self.assertEqual(f, {'He': 2})

        f = chem.EmpiricalFormula('He-2')
        self.assertEqual(f, {'He': -2})

        f = chem.EmpiricalFormula('He-20')
        self.assertEqual(f, {'He': -20})

        f = chem.EmpiricalFormula('H2O')
        self.assertEqual(f, {'H': 2, 'O': 1})

        f = chem.EmpiricalFormula('He-20He30')
        self.assertEqual(f, {'He': 10})

        f = chem.EmpiricalFormula('RaRb')
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        with self.assertRaisesRegex(ValueError, 'not a valid formula'):
            chem.EmpiricalFormula('Hee2')

        with self.assertRaisesRegex(ValueError, 'not a valid formula'):
            chem.EmpiricalFormula('h2')

    def test_EmpiricalFormula_get_attr(self):
        f = chem.EmpiricalFormula()
        self.assertEqual(f.C, 0)
        self.assertEqual(f['C'], 0)

    def test_EmpiricalFormula___setitem__(self):
        f = chem.EmpiricalFormula()
        f.C = 0
        self.assertEqual(f, {})
        self.assertEqual(dict(f), {})
        self.assertEqual(str(f), '')

        f = chem.EmpiricalFormula()
        f.A = 1
        self.assertEqual(f, {'A': 1})
        f.A = 0
        self.assertEqual(f, {})
        self.assertEqual(dict(f), {})
        self.assertEqual(str(f), '')

        f = chem.EmpiricalFormula()
        with self.assertRaisesRegex(ValueError, 'Coefficient must be an integer'):
            f.A = -1.5

    def test_EmpiricalFormula_get_molecular_weight(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertAlmostEqual(f.get_molecular_weight(), 18.015)

    def test_EmpiricalFormula___add__(self):
        f = chem.EmpiricalFormula('H2O')
        g = chem.EmpiricalFormula('HO')
        self.assertEqual(str(f + g), 'H3O2')
        self.assertEqual(str(f + 'HO'), 'H3O2')

    def test_EmpiricalFormula___sub__(self):
        f = chem.EmpiricalFormula('H2O')
        g = chem.EmpiricalFormula('HO')
        self.assertEqual(str(f - g), 'H')
        self.assertEqual(str(f - 'HO'), 'H')

    def test_EmpiricalFormula___mul__(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertEqual(str(f * 2), 'H4O2')

    def test_EmpiricalFormula___truediv__(self):
        f = chem.EmpiricalFormula('H4O2')
        self.assertEqual(f / 2, chem.EmpiricalFormula({'H': 2, 'O': 1}))

    def test_EmpiricalFormula___str__(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertEqual(str(f), 'H2O')

        f = chem.EmpiricalFormula('OH2')
        self.assertEqual(str(f), 'H2O')

        f = chem.EmpiricalFormula('N0OH2')
        self.assertEqual(str(f), 'H2O')
