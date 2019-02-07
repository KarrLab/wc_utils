""" Utility functions

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-20
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import numpy as np
import six
from wc_utils.util.list import det_dedupe


def cast_to_builtins(obj):
    """ Recursively type cast an object to a semantically equivalent object expressed using only builtin types

    * All iterable objects (objects with `__iter__` attribute) are converted to lists
    * All dictionable objects (objects which are dictionaries or which have the `__dict__` attribute) are
      converted to dictionaries

    Args:
        obj (:obj:`object`): an object

    Returns:
        :obj:`object`: a semantically equivalent object expressed using only builtin types
    """

    if isinstance(obj, dict):
        return dict((key, cast_to_builtins(val)) for key, val in obj.items())

    elif hasattr(obj, '__dict__'):
        return dict((key, cast_to_builtins(val)) for key, val in obj.__dict__.items())

    elif hasattr(obj, '__iter__') and not isinstance(obj, six.string_types):
        return [cast_to_builtins(val) for val in obj]

    if isinstance(obj, (np.bool_, np.int_, np.intc, np.intp,
                        np.int8, np.int16, np.int32, np.int64,
                        np.uint8, np.uint16, np.uint32, np.uint64,
                        np.float16, np.float32, np.float64,
                        np.complex64, np.complex128,
                        )):
        return obj.item()

    else:
        return obj


def assert_value_equal(obj1, obj2, check_type=False, check_iterable_ordering=False):
    """ Recursively raise an exception if two objects have different semantic values, ignoring

    * key/attribute order
    * optionally, object types
    * optionally, element ordering in iterables

    Args:
        obj1 (:obj:`object`): first object
        obj1 (:obj:`object`): second object
        check_type (:obj:`bool`, optional): If true, raise an exception if `obj1` and `obj2` have different types
        check_iterable_ordering (:obj:`bool`, optional): If true, raise an exception if the objects have different
            orderings of iterable attributes

    Raises:
        obj:`TypesUtilAssertionError`: If the value of `obj1` is not equal to that of `obj2`
    """

    if check_type and obj1.__class__ != obj2.__class__:
        raise TypesUtilAssertionError('Type of obj1 ({}) is not equal to that of obj2 ({})'.format(
            obj1.__class__, obj2.__class__))

    if isinstance(obj1, dict) or hasattr(obj1, '__dict__'):
        if not (isinstance(obj2, dict) or hasattr(obj2, '__dict__')):
            raise TypesUtilAssertionError(
                'obj1 has attributes/keys, but obj2 does not.\n\nobj1:\n{}\n\nobj2:\n{}'.format(obj1, obj2))

        if isinstance(obj1, dict):
            attr1 = obj1.keys()
        else:
            attr1 = vars(obj1)
        if isinstance(obj2, dict):
            attr2 = obj2.keys()
        else:
            attr2 = vars(obj2)
        if set(attr1) != set(attr2):
            raise TypesUtilAssertionError('Objects have different attributes/keys')

        for attr in attr1:
            if isinstance(obj1, dict):
                val1 = obj1[attr]
            else:
                val1 = getattr(obj1, attr)
            if isinstance(obj2, dict):
                val2 = obj2[attr]
            else:
                val2 = getattr(obj2, attr)
            assert_value_equal(val1, val2, check_type, check_iterable_ordering)

    elif (hasattr(obj1, '__iter__') and not (isinstance(obj1, dict) or hasattr(obj1, '__dict__') or
                                             isinstance(obj1, six.string_types))):
        if not ((hasattr(obj2, '__iter__') and not (isinstance(obj2, dict) or
                                                    hasattr(obj2, '__dict__') or isinstance(obj2, six.string_types)))):
            raise TypesUtilAssertionError('obj1 is iterable, but obj2 is not')

        if len(obj1) != len(obj2):
            raise TypesUtilAssertionError('Objects have different lengths')

        if check_iterable_ordering:
            for val1, val2 in zip(obj1, obj2):
                assert_value_equal(val1, val2, check_type, check_iterable_ordering)
        else:
            used2 = []
            for val1 in obj1:
                matching_val2 = False
                for i2, val2 in enumerate(obj2):
                    if i2 in used2:
                        continue
                    try:
                        assert_value_equal(val1, val2, check_type, check_iterable_ordering)
                        matching_val2 = True
                        used2.append(i2)
                        break
                    except TypesUtilAssertionError:
                        pass
                if not matching_val2:
                    raise TypesUtilAssertionError('No equivalent element {} in obj2'.format(val1))

    else:
        try:
            if np.isnan(obj1) and np.isnan(obj2):
                return
        except:
            pass

        if obj1 != obj2:
            raise TypesUtilAssertionError('Objects have different values')


def assert_value_not_equal(obj1, obj2, check_type=False, check_iterable_ordering=False):
    """ Recursively raise an exception if two objects have the same semantic values, ignoring

    * key/attribute order
    * optionally, object types
    * optionally, element ordering in iterables

    Args:
        obj1 (:obj:`object`): first object
        obj1 (:obj:`object`): second object
        check_type (:obj:`bool`, optional): If true, raise an exception if `obj1` and `obj2` have different types
        check_iterable_ordering (:obj:`bool`, optional): If true, raise an exception if the objects have different
            orderings of iterable attributes

    Raises:
        obj:`TypesUtilAssertionError`: If the value of `obj1` is not equal to that of `obj2`
    """

    try:
        assert_value_equal(obj1, obj2, check_type=check_type,
                           check_iterable_ordering=check_iterable_ordering)
    except TypesUtilAssertionError:
        return

    raise TypesUtilAssertionError('obj1 and obj2 have equal values')


def is_iterable(obj):
    """ Check if object is an iterable (list, tuple, etc.) and not a string

    Args:
        obj (:obj:`object`): object

    Returns:
        :obj:`bool`: Whether or not object is iterable
    """
    return hasattr(obj, '__iter__') \
        and not isinstance(obj, (six.string_types, dict)) \
        and not hasattr(obj, '__dict__')


def get_subclasses(cls, immediate_only=False):
    """ Reproducibly get subclasses of a class, with duplicates removed

    Args:
        cls (:obj:`type`): class
        immediate_only (:obj:`bool`, optional): if true, only return direct subclasses

    Returns:
        :obj:`list` of `type`: list of subclasses, with duplicates removed
    """
    subclasses = list(cls.__subclasses__())

    if not immediate_only:
        for sub_cls in subclasses.copy():
            subclasses.extend(get_subclasses(sub_cls, immediate_only=False))

    return det_dedupe(subclasses)


def get_superclasses(cls, immediate_only=False):
    """ Get superclasses of a class. If `immediate_only`, only return direct superclasses.

    Args:
        cls (:obj:`type`): class
        immediate_only (:obj:`bool`): if true, only return direct superclasses

    Returns:
        :obj:`list` of :obj:`type`: list of superclasses
    """
    superclasses = list(cls.__bases__)

    if not immediate_only:
        for superclass in cls.__bases__:
            superclasses += get_superclasses(superclass)

    return tuple(superclasses)


class TypesUtilAssertionError(AssertionError):
    """ Types Util assertion error """
    pass
