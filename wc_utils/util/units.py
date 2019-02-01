""" Utilities for dealing with units

:Author: Jonathan <jonrkarr@gmail.com>
:Date: 2017-05-29
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

import operator
import os
import pint
import pkg_resources

DEFAULT_UNIT_DEFINITION_FILENAME = pkg_resources.resource_filename('wc_utils', 'util/units.txt')


def get_unit_registry(base_filename='', extra_filenames=None):
    """ Get a unit registry

    Args:
        base_filename (:obj:`str`, optional): Path to base unit system definition. If :obj:`None`, the 
            default pint unit system will be used
        extra_filenames (:obj:`list` of :obj:`str`, optional): List of paths to additional unit definitions 
            beyond the base unit system definition

    Returns:
        :obj:`pint.UnitRegistry`: unit registry
    """
    unit_registry = pint.UnitRegistry(base_filename)
    extra_filenames = extra_filenames or []
    for extra_filename in extra_filenames:
        unit_registry = pint.UnitRegistry()
        unit_registry.load_definitions(extra_filename)
    return unit_registry


unit_registry = get_unit_registry(extra_filenames=[DEFAULT_UNIT_DEFINITION_FILENAME])
# :obj:`pint.UnitRegistry`: unit registry


def are_units_equivalent(units1, units2, check_same_magnitude=True):
    """ Determine if two units are equivalent

    Args:
        units1 (:obj:`pint.unit._Unit`): units
        units2 (:obj:`pint.unit._Unit`): other units
        check_same_magnitude (:obj:`bool`, optional): if :obj:`True`, units are only equivalent if they
            have the same magnitude

    Returns:
        :obj:`bool`: :obj:`True` if the units are equivalent
    """
    if units1 is None:
        if units2 is None:
            return True
        return False
    else:
        if units2 is None:
            return False
        else:
            if not isinstance(units1, (pint.unit._Unit, pint.quantity._Quantity)):
                return False
            registry = units1._REGISTRY
            if not isinstance(units2, (registry.Unit, registry.Quantity)):
                return False
            if units1 == units2:
                return True

            units1_expr = registry.parse_expression(str(units1))
            units2_expr = registry.parse_expression(str(units2))

            if check_same_magnitude:
                try:
                    return units1_expr.compare(units2_expr, operator.eq)
                except pint.DimensionalityError:
                    return False
            else:                
                return units1_expr.check(units2_expr)
