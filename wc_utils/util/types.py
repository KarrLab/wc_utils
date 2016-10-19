""" Utility functions

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-20
:Copyright: 2016, Karr Lab
:License: MIT
"""

import numpy as np
import six


class TypesUtil(object):
    """ Type utilities methods """

    @staticmethod
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
            return dict((key, TypesUtil.cast_to_builtins(val)) for key, val in obj.items())

        elif hasattr(obj, '__dict__'):
            return dict((key, TypesUtil.cast_to_builtins(val)) for key, val in obj.__dict__.items())

        elif hasattr(obj, '__iter__') and not isinstance(obj, six.string_types):
            return [TypesUtil.cast_to_builtins(val) for val in obj]

        if isinstance(obj, (np.bool_, np.int_, np.intc, np.intp,
                            np.int8, np.int16, np.int32, np.int64,
                            np.uint8, np.uint16, np.uint32, np.uint64,
                            np.float16, np.float32, np.float64,
                            np.complex64, np.complex128,
                            )):
            return obj.item()

        else:
            return obj

    @staticmethod
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
                TypesUtil.assert_value_equal(val1, val2, check_type, check_iterable_ordering)

        elif (hasattr(obj1, '__iter__') and not (isinstance(obj1, dict) or hasattr(obj1, '__dict__') or 
            isinstance(obj1, six.string_types))):
            if not ((hasattr(obj2, '__iter__') and not (isinstance(obj2, dict) or 
                hasattr(obj2, '__dict__') or isinstance(obj2, six.string_types)))):
                raise TypesUtilAssertionError('obj1 is iterable, but obj2 is not')

            if len(obj1) != len(obj2):
                raise TypesUtilAssertionError('Objects have different lengths')

            if check_iterable_ordering:
                for val1, val2 in zip(obj1, obj2):
                    TypesUtil.assert_value_equal(val1, val2, check_type, check_iterable_ordering)
            else:
                used2 = []
                for val1 in obj1:
                    matching_val2 = False
                    for i2, val2 in enumerate(obj2):
                        if i2 in used2:
                            continue
                        try:
                            TypesUtil.assert_value_equal(val1, val2, check_type, check_iterable_ordering)
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

    @staticmethod
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
            TypesUtil.assert_value_equal(obj1, obj2, check_type=check_type, check_iterable_ordering=check_iterable_ordering)
        except TypesUtilAssertionError:
            return

        raise TypesUtilAssertionError('obj1 and obj2 have equal values')


class TypesUtilAssertionError(AssertionError):
    """ Assertion error """
    pass
