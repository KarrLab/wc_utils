""" Miscellaneous utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-05
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import six
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
    return isclass_by_name(most_qual_cls_name(cls), cls_info)


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
        elif cls_name == most_qual_cls_name(a_cls_info):
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
    if isinstance(obj, six.class_types):
        cls = obj
    else:
        cls = obj.__class__

    if (3, 3) <= sys.version_info:
        return cls.__module__ + '.' + cls.__qualname__
    else:
        return cls.__module__ + '.' + cls.__name__


def round_direct(value, precision=2):
    '''Convert `value` to rounded string with appended sign indicating the rounding direction.

    Append '+' to indicate that `value` has been rounded down, and '-' to indicate rounding up.
    For example, 
    round_direct(3.01, 2) == '3.01'
    round_direct(3.01, 1) == '3.0+'
    round_direct(2.99, 1) == '3.0-'

    This function helps display simulation times that have been slightly increased or decreased to
    control order execution.

    Args:
        value (float): the value to round.
        precision (int): the precision with which to round `value`.

    Returns:
        str: `value` rounded to `precision` places, followed by a sign indicating rounding direction.
    '''
    if round(value, precision) == value:
        return str(round(value, precision))
    elif round(value, precision) < value:
        return '{}+'.format(round(value, precision))
    else:   # value < round(value, precision)
        return '{}-'.format(round(value, precision))


def quote(s):
    """ Enclose a string that contains spaces in single quotes, 'like this'

    Args:
        s (:obj:`str`): a string

    Returns:
        :obj:`str`: a string
    """
    if ' ' in s:
        return "'{}'".format(s)
    else:
        return s

def obj_to_str(obj, attrs):
    rv = ['Class: ' + obj.__class__.__name__]
    for attr in attrs:
        rv.append("{}: {}".format(attr, str(getattr(obj, attr))))
    return '\n'.join(rv)

class OrderableNoneType(object):
    """ Type than can be used for sorting in Python 3 in place of :obj:`None` """

    def __lt__(self, other):
        return (other is not self) and (other is not None)

    def __le__(self, other):
        return True

    def __eq__(self, other):
        return (other is self) or (other is None)

    def __ge__(self, other):
        return (other is self) or (other is None)

    def __gt__(self, other):
        return False

OrderableNone = OrderableNoneType()
# Object than can be used for sorting in Python 3 in place of :obj:`None`
