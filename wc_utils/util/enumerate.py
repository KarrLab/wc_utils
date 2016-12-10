""" Enumerations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-12-09
:Copyright: 2016, Karr Lab
:License: MIT
"""

from enum import Enum, EnumMeta, _EnumDict
from six import with_metaclass


class _CaseInsensitiveEnumDict(_EnumDict):

    def __setitem__(self, key, value):
        super(_CaseInsensitiveEnumDict, self).__setitem__(key.lower(), value)


class CaseInsensitiveEnumMeta(EnumMeta):

    @classmethod
    def __prepare__(metacls, cls, bases):
        return _CaseInsensitiveEnumDict()

    def __new__(metacls, cls, bases, classdict):
        if isinstance(classdict, _CaseInsensitiveEnumDict):
            lower_classdict = classdict
        else:
            lower_classdict = {key.lower(): val for key, val in dict(classdict).items()}
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
