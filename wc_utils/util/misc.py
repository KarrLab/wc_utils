""" Miscellaneous utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-05
:Copyright: 2016, Karr Lab
:License: MIT
"""

import sys

def isclass(cls, cls_info):
    """Compares a class with classes in `cls_info`.

    Args:
        cls (:obj:`str`): class
        cls_info (:obj:`class`, :obj:`type`, or :obj:`tuple` of classes and types): class, type, or
            tuple of classes and types

    Returns:
        :obj:`bool`: True if one of the classes in `cls_info` is `cls`.
    """
    return isclass_by_name(cls.__name__, cls_info)


def isclass_by_name(cls_name, cls_info):
    """Compares a class name with the names of the classes in `cls_info`.

    Args:
        cls_name (:obj:`str`): class name
        cls_info (:obj:`class`, :obj:`type`, or :obj:`tuple` of classes and types): class, type, or
            tuple of classes and types

    Returns:
        :obj:`bool`: True if one of the classes in `cls_info` has name `cls_name`.
    """

    if not isinstance(cls_info, tuple):
        cls_info = (cls_info,)

    for a_cls_info in cls_info:
        if isinstance(a_cls_info, tuple):
            if isclass_by_name(cls_name, a_cls_info):
                return True
        elif cls_name == a_cls_info.__name__:
            return True

    return False

def most_qual_cls_name(obj):
    """Obtain the most qualified class name available for `obj`.

    Since references to classes cannot be sent in messages that leave an address space,
    use the most qualified class name available to compare class values across address spaces.
    Fully qualified class names are available for Python >= 3.3.

    Args:
        obj (:obj:`class`): an object, which may be a class.

    Returns:
        :obj:`str`: the most qualified class name available for `obj`.
    """
    if isinstance(obj, type):
        cls = obj
    else:
        cls = obj.__class__

    if (3,3) <= sys.version_info:
        return cls.__module__ + '.' + cls.__qualname__
    else:
        return cls.__module__ + '.' + cls.__name__
