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
    jnius_config.add_classpath(pkg_resources.resource_filename('wc_utils', 'util/chem/DrawMolecule.jar'))
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

    def __hash__(self):
        """ Generate a hash

        Returns:
            :obj:`int`: hash
        """
        return hash(str(self))


def get_major_micro_species(structure_or_structures, in_format, out_format,
                            ph=7.4, major_tautomer=False, keep_hydrogens=False, dearomatize=False):
    """ Get the major protonation state of one or more compounds at a specific pH.

    Args:
        structure_or_structures (:obj:`str` or :obj:`list` of :obj:`str`): chemical structure or 
            list of chemical structures
        in_format (:obj:`str`): format of :obj:`structure_or_structures` (e.g. 'inchi' or 'smiles')
        out_format (:obj:`str`): format of output (e.g. 'inchi' or 'smiles')
        ph (:obj:`float`, optional): pH at which to calculate major protonation microspecies
        major_tautomer (:obj:`bool`, optional): if :obj:`True`, use the major tautomeric in the calculation
        keep_hydrogens (:obj:`bool`, optional): if :obj:`True`, keep explicity defined hydrogens
        dearomatize (:obj:`bool`, optional): if :obj:`True`, dearomatize molecule

    Returns:
        :obj:`str` or :obj:`list` of :obj:`str`: protonated chemical structure or
            list of protonated chemical structures
    """
    JavaGetMajorMicroSpecies = jnius.autoclass('GetMajorMicroSpecies')
    ph = float(ph)

    if isinstance(structure_or_structures, str):
        result = JavaGetMajorMicroSpecies.run_one(structure_or_structures, in_format, out_format,
                                                  ph, major_tautomer, keep_hydrogens, dearomatize)
        if out_format in ['inchi', 'smiles']:
            result = result.partition('\n')[0].strip()
    else:
        result = JavaGetMajorMicroSpecies.run_multiple(structure_or_structures, in_format, out_format,
                                                       ph, major_tautomer, keep_hydrogens, dearomatize)
        if out_format in ['inchi', 'smiles']:
            result = [r.partition('\n')[0].strip() for r in result]

    return result


def draw_molecule(structure, format, image_format='svg', atom_labels=None, atom_sets=None, bond_sets=None,
                  show_atom_nums=False, width=200, height=200, include_xml_header=True):
    """ Draw an image of a molecule

    Args:
        structure (:obj:`str`): chemical structure
        format (:obj:`str`): format of :obj:`structure` (e.g. 'inchi' or 'smiles')
        image_format (:obj:`str`, optional): format of generated image {emf, eps, jpeg, msbmp, pdf, png, or svg}
        atom_labels (:obj:`list` of :obj:`dict`, optional): list of atom labels (dictionaries with keys 
            {`position`, `element`, `label`, `color`})
        atom_sets (:obj:`list` of :obj:`dict`, optional): list of atom sets (dictionaries with keys 
            {`positions`, `elements`, `color`})
        bond_sets (:obj:`list` of :obj:`dict`, optional): list of bond sets (dictionaries with keys 
            {`positions`, `elements`, `color`})
        show_atom_nums (:obj:`bool`, optional): if :obj:`True`, show the numbers of the atoms
        width (:obj:`int`, optional): width in pixels
        height (:obj:`int`, optional): height in pixels
        include_xml_header (:obj:`bool`, optional): if :obj:`True`, include XML header

    Returns:
        :obj:`str`: image of chemical structure
    """
    atom_labels = atom_labels or []
    atoms_to_label = []
    atom_label_elements = []
    atom_label_texts = []
    atom_label_colors = []
    for atom_label in atom_labels:
        if atom_label['label']:
            atoms_to_label.append(atom_label['position'])
            atom_label_elements.append(atom_label['element'])
            atom_label_texts.append(atom_label['label'])
            atom_label_colors.append(atom_label['color'])

    atom_sets = atom_sets or []
    atom_set_positions = []
    atom_set_elements = []
    atom_set_colors = []
    for atom_set in atom_sets:
        atom_set_positions.append(atom_set['positions'])
        atom_set_elements.append(atom_set['elements'])
        atom_set_colors.append(atom_set['color'])

    if not atom_set_positions:
        atom_set_positions = [[0]]
        atom_set_elements = [['']]

    bond_sets = bond_sets or []
    bond_set_positions = []
    bond_set_elements = []
    bond_set_colors = []
    for bond_set in bond_sets:
        bond_set_positions.append(bond_set['positions'])
        bond_set_elements.append(bond_set['elements'])
        bond_set_colors.append(bond_set['color'])

    if not bond_set_positions:
        bond_set_positions = [[[0]]]
        bond_set_elements = [[['']]]

    JavaDrawMolecule = jnius.autoclass('DrawMolecule')
    image = JavaDrawMolecule.run(structure, format, image_format,
                                 atoms_to_label, atom_label_elements, atom_label_texts, atom_label_colors,
                                 atom_set_positions, atom_set_elements, atom_set_colors,
                                 bond_set_positions, bond_set_elements, bond_set_colors,
                                 show_atom_nums, width, height, include_xml_header)
    if isinstance(image, jnius.jnius.ByteArray):
        image = image.tostring()
    return image


class OpenBabelUtils(object):
    @staticmethod
    def get_formula(mol):
        """ Get the formula of an OpenBabel molecule

        Args:
            mol (:obj:`openbabel.OBMol`): molecule

        Returns:
            :obj:`EmpiricalFormula`: formula
        """
        return EmpiricalFormula(mol.GetFormula().strip('-+'))

    @classmethod
    def get_inchi(cls, mol, options=('r', 'F',)):
        """ Get the InChI-encoded structure of an OpenBabel molecule

        Args:
            mol (:obj:`openbabel.OBMol`): molecule
            options (:obj:`list` of :obj:`str`, optional): export options

        Returns:
            :obj:`str`: InChI-encoded structure
        """
        conversion = openbabel.OBConversion()
        assert conversion.SetOutFormat('inchi'), 'Unable to set format to InChI'
        for option in options:
            conversion.SetOptions(option, conversion.OUTOPTIONS)
        inchi = conversion.WriteString(mol).strip()
        inchi = inchi.replace('InChI=1/', 'InChI=1S/')
        inchi = inchi.partition('/f')[0]
        return inchi

    @classmethod
    def get_smiles(cls, mol, options=()):
        """ Get the SMILES-encoded structure of an OpenBabel molecule

        Args:
            mol (:obj:`openbabel.OBMol`): molecule
            options (:obj:`list` of :obj:`str`, optional): export options

        Returns:
            :obj:`str`: SMILES-encoded structure
        """
        conversion = openbabel.OBConversion()
        assert conversion.SetOutFormat('smiles'), 'Unable to set format to Daylight SMILES'
        for option in options:
            conversion.SetOptions(option, conversion.OUTOPTIONS)
        return conversion.WriteString(mol).partition('\t')[0].strip()

    @classmethod
    def export(cls, mol, format, options=()):
        """ Export an OpenBabel molecule to format

        Args:
            mol (:obj:`openbabel.OBMol`): molecule
            format (:obj:`str`): format
            options (:obj:`list` of :obj:`str`, optional): export options

        Returns:
            :obj:`str`: format representation of molecule
        """
        if format == 'inchi':
            return cls.get_inchi(mol, options=options)
        if format in ['smi', 'smiles']:
            return cls.get_smiles(mol, options=options)

        conversion = openbabel.OBConversion()
        assert conversion.SetOutFormat(format), 'Unable to set format to {}'.format(format)
        for option in options:
            conversion.SetOptions(option, conversion.OUTOPTIONS)
        return conversion.WriteString(mol).strip()
