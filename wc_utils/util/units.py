""" Utilities for dealing with units

:Author: Jonathan <jonrkarr@gmail.com>
:Date: 2017-05-29
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

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
