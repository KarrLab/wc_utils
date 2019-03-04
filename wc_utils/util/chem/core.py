""" Chemistry utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

import attrdict
import mendeleev
import os
import pkg_resources
import re
import subprocess
import time

try:
    import jnius_config
    classpath = os.getenv('CLASSPATH', None)
    if classpath:
        classpath = classpath.split(':')
        jnius_config.set_classpath(*classpath)
    jnius_config.add_classpath(pkg_resources.resource_filename('wc_utils', 'util/chem/GetMajorMicroSpecies.jar'))
    import jnius
except ModuleNotFoundError:  # pragma: no cover
    pass  # pragma: no cover

try:
    import openbabel
except ModuleNotFoundError:  # pragma: no cover
    pass  # pragma: no cover


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


class GetMajorMicroSpecies(object):
    @classmethod
    def run(cls, structure_or_structures, format='inchi',
            ph=7.4, major_tautomer=False, keep_hydrogens=False):
        """ Get the major protonation state of one or more compounds at a specific pH.

        Args:
            structure_or_structures (:obj:`str` or :obj:`list` of :obj:`str`): InChI-encoded chemical or 
                list of InChI-encoded chemical structures
            format (:obj:`str`, optional): format of :obj:`structure_or_structures` (e.g. 'inchi' or 'smiles')
            ph (:obj:`float`, optional): pH at which to calculate major protonation microspecies
            major_tautomer (:obj:`bool`, optional): if :obj:`True`, use the major tautomeric in the calculation
            keep_hydrogens (:obj:`bool`, optional): if :obj:`True`, keep explicity defined hydrogens

        Returns:
            :obj:`str` or :obj:`list` of :obj:`str`: InChI-encoded protonated chemical structure or
                list of InChI-encoded protonated chemical structures
        """
        JavaGetMajorMicroSpecies = jnius.autoclass('GetMajorMicroSpecies')

        if isinstance(structure_or_structures, str):
            result = JavaGetMajorMicroSpecies.run_one(structure_or_structures, format, format,
                                                      ph, major_tautomer, keep_hydrogens)
            if format in ['inchi', 'smiles']:
                result = result.partition('\n')[0].strip()
        else:
            result = JavaGetMajorMicroSpecies.run_multiple(structure_or_structures, format, format,
                                                           ph, major_tautomer, keep_hydrogens)
            if format in ['inchi', 'smiles']:
                result = [r.partition('\n')[0].strip() for r in result]

        return result


class OpenBabelUtils(object):
    @staticmethod
    def get_formula(mol):
        """ Get the formula of an OpenBabel molecule

        Args:
            mol (:obj:`openbabel.OBMol`): molecule

        Returns:
            :obj:`EmpiricalFormula`: formula
        """
        el_table = openbabel.OBElementTable()
        formula = {}
        mass = 0
        for i_atom in range(mol.NumAtoms()):
            atom = mol.GetAtom(i_atom + 1)
            el = el_table.GetSymbol(atom.GetAtomicNum())
            if el in formula:
                formula[el] += 1
            else:
                formula[el] = 1
            mass += el_table.GetMass(atom.GetAtomicNum())
        formula = EmpiricalFormula(formula)

        # calc hydrogens because OpenBabel doesn't output this
        formula['H'] = round((mol.GetMolWt() - mass) / el_table.GetMass(1))
        return formula

    @staticmethod
    def get_inchi(mol):
        """ Get the InChI-encoded structure of an OpenBabel molecule

        Args:
            mol (:obj:`openbabel.OBMol`): molecule

        Returns:
            :obj:`str`: InChI-encoded structure
        """
        conversion = openbabel.OBConversion()
        assert conversion.SetOutFormat('inchi'), 'Unable to set format to InChI'
        conversion.SetOptions('r', conversion.OUTOPTIONS)
        conversion.SetOptions('F', conversion.OUTOPTIONS)
        inchi = conversion.WriteString(mol).strip()
        inchi = inchi.replace('InChI=1/', 'InChI=1S/')
        i_fixed_h = inchi.find('/f')
        if i_fixed_h >= 0:
            inchi = inchi[0:i_fixed_h]
        return inchi

    @staticmethod
    def get_smiles(mol):
        """ Get the Daylight SMILES-encoded structure of an OpenBabel molecule

        Args:
            mol (:obj:`openbabel.OBMol`): molecule

        Returns:
            :obj:`str`: Daylight SMILES-encoded structure
        """
        conversion = openbabel.OBConversion()
        assert conversion.SetOutFormat('smi'), 'Unable to set format to Daylight SMILES'
        smiles = conversion.WriteString(mol).strip()
        return smiles
