""" Tests of the chemistry utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_utils.util import chem
import attrdict
import mock
import unittest


class EmpiricalFormulaTestCase(unittest.TestCase):

    def test_EmpiricalFormula_constructor(self):
        f = chem.EmpiricalFormula()
        self.assertEqual(f, {})

        f = chem.EmpiricalFormula('H')
        self.assertEqual(f, {'H': 1})

        f = chem.EmpiricalFormula('H2')
        self.assertEqual(f, {'H': 2})

        f = chem.EmpiricalFormula('H2.5')
        self.assertEqual(f, {'H': 2.5})

        f = chem.EmpiricalFormula('H2.5e3')
        self.assertEqual(f, {'H': 2.5e3})

        f = chem.EmpiricalFormula('H-2.5e3')
        self.assertEqual(f, {'H': -2.5e3})

        f = chem.EmpiricalFormula('H2.5e+3')
        self.assertEqual(f, {'H': 2.5e3})

        f = chem.EmpiricalFormula('H2.5e-3')
        self.assertEqual(f, {'H': 2.5e-3})

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

        f = chem.EmpiricalFormula(attrdict.AttrDict({'Ra': 1, 'Rb': 1}))
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        f = chem.EmpiricalFormula(attrdict.AttrDefault(int, {'Ra': 1, 'Rb': 1}))
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        f = chem.EmpiricalFormula(chem.EmpiricalFormula('RaRb'))
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
        f.A = 1.5
        self.assertEqual(f, {'A': 1.5})

        f = chem.EmpiricalFormula()
        with self.assertRaisesRegex(ValueError, 'Coefficient must be a float'):
            f.A = 'a'

        f = chem.EmpiricalFormula()
        with self.assertRaisesRegex(ValueError, 'Element must be a one or two letter string'):
            f.Aaa = 1

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

        f = chem.EmpiricalFormula('H2O1.1')
        self.assertEqual(str(f), 'H2O1.1')

        f = chem.EmpiricalFormula('H2O1.1e-3')
        self.assertEqual(str(f), 'H2O0.0011')

        f = chem.EmpiricalFormula('H2O1.1e+3')
        self.assertEqual(str(f), 'H2O1100')

        f = chem.EmpiricalFormula('H2O-1.1e+3')
        self.assertEqual(str(f), 'H2O-1100')

    def test_EmpiricalFormula___contains__(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertIn('H', f)
        self.assertIn('C', f)
        self.assertNotIn('Ccc', f)


class ProtonationTestCase(unittest.TestCase):
    GLY = 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)'

    def test(self):
        self.assertEqual(chem.get_major_protonation_state(self.GLY, ph=2.), 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p+1')
        self.assertEqual(chem.get_major_protonation_state([self.GLY, self.GLY], ph=13.), [
            'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p-1',
            'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p-1',
        ])

    def test_errors(self):
        with self.assertRaises(ValueError):
            chem.get_major_protonation_state(self.GLY + '\n' + self.GLY, ph=2.)

        with self.assertRaises(ValueError):
            chem.get_major_protonation_state([self.GLY + '\n' + self.GLY], ph=2.)

        return_value = mock.Mock()
        return_value.poll = lambda: True
        return_value.communicate = lambda: (''.encode(), ''.encode())
        return_value.returncode = 1
        with mock.patch('subprocess.Popen', return_value=return_value):
            with self.assertRaises(ValueError):
                chem.get_major_protonation_state(self.GLY, ph=2.)
