""" Test of unit utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-29
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

from wc_utils.util import units
import pint
import unittest


class TestUnits(unittest.TestCase):

    def test_get_unit_registry(self):
        ureg = units.get_unit_registry()
        self.assertIsInstance(ureg, pint.UnitRegistry)

        quantity = ureg.parse_expression('s^(-1)')
        self.assertEqual(str(quantity.units), '1 / second')

        self.assertRaises(pint.UndefinedUnitError, ureg.parse_expression, 'M')

    def test_unit_registry(self):
        ureg = units.unit_registry
        self.assertIsInstance(ureg, pint.UnitRegistry)

        quantity = ureg.parse_expression('s^(-1)')
        self.assertEqual(str(quantity.units), '1 / second')

        quantity = 1.5 * ureg.parse_expression('M')
        self.assertEqual(str(quantity.units), 'molar')

        self.assertEqual(str(quantity.to(ureg('mole / liter')).units), 'mole / liter')

        self.assertAlmostEqual((2.5 * ureg('enzyme_unit')).to('kat').magnitude, 2.5 / 60 * 1e-6)
        self.assertAlmostEqual((2.5 * ureg('U')).to('kat').magnitude, 2.5 / 60 * 1e-6)
        self.assertAlmostEqual(str((2.5 * ureg('U')).to('kat').units), 'katal')
