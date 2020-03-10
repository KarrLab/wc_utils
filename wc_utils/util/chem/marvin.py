""" Chemistry utilities from ChemAxon Marvin

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2020-01-07
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import os
import pkg_resources
import re

try:
    import jnius_config

    opts = os.getenv('JAVA_OPTS', None)
    if opts:
        opts = re.split(r' +', opts)
        jnius_config.add_options(*opts)

    classpath = os.getenv('CLASSPATH', None)
    if classpath:
        classpath = classpath.split(':')
        jnius_config.set_classpath(*classpath)
    jnius_config.add_classpath(pkg_resources.resource_filename('wc_utils', 'util/chem/GetMajorMicroSpecies.jar'))
    jnius_config.add_classpath(pkg_resources.resource_filename('wc_utils', 'util/chem/DrawMolecule.jar'))
except (ModuleNotFoundError, KeyError, SystemError):  # pragma: no cover
    pass  # pragma: no cover

try:
    import jnius
    JavaGetMajorMicroSpecies = jnius.autoclass('GetMajorMicroSpecies')
    JavaDrawMolecule = jnius.autoclass('DrawMolecule')
except ModuleNotFoundError:  # pragma: no cover
    JavaGetMajorMicroSpecies = None
    JavaDrawMolecule = None


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
    ph = float(ph)

    if not JavaGetMajorMicroSpecies:
        raise ModuleNotFoundError("ChemAxon Marvin and pyjnius must be installed")

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


def draw_molecule(structure, format, image_format='svg', atom_labels=None, atom_label_font_size=0.4,
                  atom_sets=None, bond_sets=None,
                  show_atom_nums=False, width=200, height=200, include_xml_header=True):
    """ Draw an image of a molecule

    Args:
        structure (:obj:`str`): chemical structure
        format (:obj:`str`): format of :obj:`structure` (e.g. 'inchi' or 'smiles')
        image_format (:obj:`str`, optional): format of generated image {emf, eps, jpeg, msbmp, pdf, png, or svg}
        atom_labels (:obj:`list` of :obj:`dict`, optional): list of atom labels (dictionaries with keys 
            {`position`, `element`, `label`, `color`})
        atom_label_font_size (:obj:`float`, optional): font size of atom labels
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

    if not JavaDrawMolecule:
        raise ModuleNotFoundError("ChemAxon Marvin and pyjnius must be installed")
    image = JavaDrawMolecule.run(structure, format, image_format,
                                 atoms_to_label, atom_label_elements, atom_label_texts, atom_label_colors,
                                 atom_label_font_size,
                                 atom_set_positions, atom_set_elements, atom_set_colors,
                                 bond_set_positions, bond_set_elements, bond_set_colors,
                                 show_atom_nums, width, height, include_xml_header)
    if isinstance(image, jnius.jnius.ByteArray):
        image = image.tostring()
    return image
