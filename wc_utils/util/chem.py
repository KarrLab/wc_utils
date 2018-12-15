""" Chemistry utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

import attrdict
import mendeleev
import re


class EmpiricalFormula(attrdict.AttrDefault):
    """ An empirical formula """

    def __init__(self, value=''):
        """
        Args:
            value (:obj:`dict` or :obj:`str`): dictionary or string representation of the formula

        Raises:
            :obj:`ValueError`: if :obj:`value` is not a valid formula
        """
        super(EmpiricalFormula, self).__init__(float)

        if isinstance(value, (dict, attrdict.AttrDict, attrdict.AttrDefault)):
            for element, coefficient in value.items():
                self[element] = coefficient
        else:
            if not re.match(r'^(([A-Z][a-z]?)(\-?[0-9]+(\.?[0-9]*)?(e[\-\+]?[0-9]*)?)?)*$', value):
                raise ValueError('"{}" is not a valid formula'.format(value))

            for element, coefficient, _, _ in re.findall(r'([A-Z][a-z]?)(\-?[0-9]+(\.?[0-9]*)?(e[\-\+]?[0-9]*)?)?', value):
                self[element] += float(coefficient or '1')

    def __setitem__(self, element, coefficient):
        """ Set the count of an element

        Args:
            element (:obj:`str`): element symbol
            coefficient (:obj:`float`): element coefficient

        Raises:
            :obj:`ValueError`: if the coefficient is not a float
        """
        if not re.match(r'^[A-Z][a-z]?$', element):
            raise ValueError('Element must be a one or two letter string')

        try:
            coefficient = float(coefficient)
        except ValueError:
            raise ValueError('Coefficient must be a float')

        super(EmpiricalFormula, self).__setitem__(element, coefficient)
        if coefficient == 0.:
            self.pop(element)

    def get_molecular_weight(self):
        """ Get the molecular weight

        Returns:
            :obj:`float`: molecular weight
        """
        mw = 0.
        for element, coefficient in self.items():
            mw += mendeleev.element(element).atomic_weight * coefficient
        return mw

    def __str__(self):
        """ Generate a string representation of the formula """
        vals = []
        for element, coefficient in self.items():
            if coefficient == 0.:
                pass  # pragma: no cover # unreachable due to `__setitem__`
            elif coefficient == 1.:
                vals.append(element)
            elif coefficient == int(coefficient):
                vals.append(element + str(int(coefficient)))
            else:
                vals.append(element + str(coefficient))
        vals.sort()
        return ''.join(vals)

    def __contains__(self, element):
        """
        Args:
            element (:obj:`str`): element symbol

        Returns:
            :obj:`bool`: :obj:`True` if the empirical formula contains the element
        """
        return re.match(r'^[A-Z][a-z]?$', element) is not None

    def __add__(self, other):
        """ Add two empirical formulae

        Args:
            other (:obj:`EmpiricalFormula` or :obj:`str`): another empirical formula

        Returns:
            :obj:`EmpiricalFormula`: sum of the empirical formulae
        """

        if isinstance(other, str):
            other = EmpiricalFormula(other)

        sum = EmpiricalFormula()
        for element, coefficient in self.items():
            sum[element] = coefficient
        for element, coefficient in other.items():
            sum[element] += coefficient

        return sum

    def __sub__(self, other):
        """ Subtract two empirical formulae

        Args:
            other (:obj:`EmpiricalFormula` or :obj:`str`): another empirical formula

        Returns:
            :obj:`EmpiricalFormula`: difference of the empirical formulae
        """
        if isinstance(other, str):
            other = EmpiricalFormula(other)

        diff = EmpiricalFormula()
        for element, coefficient in self.items():
            diff[element] = coefficient
        for element, coefficient in other.items():
            diff[element] -= coefficient

        return diff

    def __mul__(self, quantity):
        """ Subtract two empirical formulae

        Args:
            quantity (:obj:`float`)

        Returns:
            :obj:`EmpiricalFormula`: multiplication of the empirical formula by :obj:`quantity`
        """
        result = EmpiricalFormula()
        for element, coefficient in self.items():
            result[element] = quantity * coefficient

        return result

    def __div__(self, quantity):
        """ Subtract two empirical formulae (for Python 2)

        Args:
            quantity (:obj:`float`)

        Returns:
            :obj:`EmpiricalFormula`: division of the empirical formula by :obj:`quantity`
        """
        return self.__truediv__(quantity)  # pragma: no cover # only used in Python 2

    def __truediv__(self, quantity):
        """ Subtract two empirical formulae

        Args:
            quantity (:obj:`float`)

        Returns:
            :obj:`EmpiricalFormula`: division of the empirical formula by :obj:`quantity`
        """
        result = EmpiricalFormula()
        for element, coefficient in self.items():
            result[element] = coefficient / quantity

        return result
