""" Enumerations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-12-09
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from enum import Enum, EnumMeta, _EnumDict
from six import with_metaclass


class _CaseInsensitiveEnumDict(_EnumDict):

    def __setitem__(self, key, value):
        # For Python 3
        super(_CaseInsensitiveEnumDict, self).__setitem__(key.lower(), value)


class CaseInsensitiveEnumMeta(EnumMeta):

    @classmethod
    def __prepare__(metacls, cls, bases):
        # For Python 3
        return _CaseInsensitiveEnumDict()

    def __new__(metacls, cls, bases, classdict):
        if isinstance(classdict, _CaseInsensitiveEnumDict):
            # For Python 3
            lower_classdict = classdict
        else:
            # For Python 2
            lower_classdict = {key.lower(): val for key, val in dict(classdict).items()}  # pragma: no cover # Python 2 only
        return super(CaseInsensitiveEnumMeta, metacls).__new__(metacls, cls, bases, lower_classdict)

    def __getattr__(cls, name):
        """ Get value by name

        Args:
            name (:obj:`str`): attribute name

        Returns:
            :obj:`Enum`: enumeration
        """
        return super(CaseInsensitiveEnumMeta, cls).__getattr__(name.lower())

    def __getitem__(cls, name):
        """ Get value by name

        Args:
            name (:obj:`str`): attribute name

        Returns:
            :obj:`Enum`: enumeration
        """
        return super(CaseInsensitiveEnumMeta, cls).__getitem__(name.lower())


class CaseInsensitiveEnum(with_metaclass(CaseInsensitiveEnumMeta, Enum)):
    """ Enumeration with case-insensitive attribute lookup """
    pass
