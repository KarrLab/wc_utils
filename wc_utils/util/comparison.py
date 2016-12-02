""" Comparison functions

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-18
:Copyright: 2016, Karr Lab
:License: MIT
"""

from collections import OrderedDict
import numpy as np
# todo: test

float_types = (float, np.float16, np.float32, np.float64, np.float128, )


def nanequal(a, b):
    return a == b or (isinstance(a, float_types) and isinstance(b, float_types) and np.isnan(a) and np.isnan(b))


class EqualityMixin(object):
    """ Provide support for equality comparisons """

    class Meta(object):
        equality_attributes = ()
        #:obj:`tuple`: list of attributes to check for semantic equality

    def __eq__(self, other):
        """ Determines if two objects are semanticaly equal

        Args:
            self (:obj:`obj`): primary object
            other (:obj:`obj`): second object

        Returns:
            :obj:`bool`: true if objects are semantically equal
        """
        if self is other:
            return True

        if not isinstance(other, self.__class__):
            return False

        for attr in self.Meta.equality_attributes:
            self_val = getattr(self, attr)
            other_val = getattr(other, attr)

            if not isinstance(other_val, self_val.__class__):
                return False

            if isinstance(self_val, set):
                if len(self_val) != len(other_val):
                    return False

                other_val = list(other_val)
                for self_val_sub in self_val:
                    matched = False
                    for other_val_sub in other_val:
                        if nanequal(self_val_sub, other_val_sub):
                            other_val.remove(other_val_sub)
                            matched = True
                            break
                    if not matched:
                        return False

            elif isinstance(self_val, (list, tuple)):
                if len(self_val) != len(other_val):
                    return False

                for self_val_sub, other_val_sub in zip(self_val, other_val):
                    if not nanequal(self_val_sub, other_val_sub):
                        return False

            elif isinstance(self_val, (dict, OrderedDict)):
                if len(self_val) != len(other_val):
                    return False

                for key in self_val:
                    if not nanequal(self_val[key], other_val[key]):
                        return False

            elif not nanequal(self_val, other_val):
                return False

        return True

    def __ne__(self, other):
        """ Determines if two objects are semanticaly unequal

        Args:
            self (:obj:`obj`): primary object
            other (:obj:`obj`): second object

        Returns:
            :obj:`bool`: true if objects are semantically unequal
        """
        return not (self == other)
