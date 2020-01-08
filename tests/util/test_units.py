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

        with self.assertRaises(pint.UndefinedUnitError):
            ureg.parse_expression('NOT_A_UNIT')

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

    def test_are_units_equivalent(self):
        registry1 = units.unit_registry
        registry2 = pint.UnitRegistry()
        registry3 = pint.UnitRegistry()

        self.assertTrue(units.are_units_equivalent(registry1.parse_units('g'), registry1.parse_units('g')))
        self.assertFalse(units.are_units_equivalent(registry1.parse_units('g'), registry2.parse_units('g')))
        self.assertTrue(units.are_units_equivalent(registry1.parse_units('g'), registry1.parse_units('g / l * l')))
        self.assertFalse(units.are_units_equivalent(registry1.parse_units('g'), registry2.parse_units('g / l * l')))
        self.assertTrue(units.are_units_equivalent(registry1.parse_units('M'), registry1.parse_units('mol / l')))
        self.assertTrue(units.are_units_equivalent(None, None))
        self.assertFalse(units.are_units_equivalent(None, registry1.parse_units('mol / l')))
        self.assertFalse(units.are_units_equivalent('g', registry1.parse_units('mol / l')))
        self.assertFalse(units.are_units_equivalent(registry1.parse_units('mol / l'), None))
        self.assertFalse(units.are_units_equivalent(registry1.parse_units('g'), registry1.parse_units('l'),
                                                    check_same_magnitude=True))
        self.assertFalse(units.are_units_equivalent(registry1.parse_units('g'), registry1.parse_units('l'),
                                                    check_same_magnitude=False))
        self.assertFalse(units.are_units_equivalent(registry1.parse_units('ag'), registry1.parse_units('g'),
                                                    check_same_magnitude=True))
        self.assertTrue(units.are_units_equivalent(registry1.parse_units('ag'), registry1.parse_units('g'),
                                                   check_same_magnitude=False))

        self.assertTrue(units.are_units_equivalent(
            registry1.parse_units('mole / liter / molar / second'),
            registry1.parse_units('1 / second')))

        self.assertFalse(units.are_units_equivalent(
            registry1.parse_units('molecule'),
            registry1.parse_units('liter * molar')))
        self.assertTrue(units.are_units_equivalent(
            registry1.parse_units('molecule / (molecule / mole)'),
            registry1.parse_units('liter * molar')))

        self.assertFalse(units.are_units_equivalent(
            registry1.parse_units('molecule'),
            registry1.parse_units('dimensionless')))
