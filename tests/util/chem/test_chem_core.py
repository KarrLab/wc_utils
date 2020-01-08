""" Tests of the chemistry utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_utils.util import chem
from wc_utils.util.chem import marvin
import attrdict
import imghdr
import mock
import openbabel
import os
import tempfile
import unittest


class EmpiricalFormulaTestCase(unittest.TestCase):

    def test_EmpiricalFormula_constructor(self):
        f = chem.EmpiricalFormula()
        self.assertEqual(f, {})

        f = chem.EmpiricalFormula('H')
        self.assertEqual(f, {'H': 1})

        f = chem.EmpiricalFormula('H2')
        self.assertEqual(f, {'H': 2})

        f = chem.EmpiricalFormula('H2.5')
        self.assertEqual(f, {'H': 2.5})

        f = chem.EmpiricalFormula('H2.5e3')
        self.assertEqual(f, {'H': 2.5e3})

        f = chem.EmpiricalFormula('H-2.5e3')
        self.assertEqual(f, {'H': -2.5e3})

        f = chem.EmpiricalFormula('H2.5e+3')
        self.assertEqual(f, {'H': 2.5e3})

        f = chem.EmpiricalFormula('H2.5e-3')
        self.assertEqual(f, {'H': 2.5e-3})

        f = chem.EmpiricalFormula('He2')
        self.assertEqual(f, {'He': 2})

        f = chem.EmpiricalFormula('He-2')
        self.assertEqual(f, {'He': -2})

        f = chem.EmpiricalFormula('He-20')
        self.assertEqual(f, {'He': -20})

        f = chem.EmpiricalFormula('H2O')
        self.assertEqual(f, {'H': 2, 'O': 1})

        f = chem.EmpiricalFormula('He-20He30')
        self.assertEqual(f, {'He': 10})

        f = chem.EmpiricalFormula('RaRb')
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        f = chem.EmpiricalFormula(attrdict.AttrDict({'Ra': 1, 'Rb': 1}))
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        f = chem.EmpiricalFormula(attrdict.AttrDefault(int, {'Ra': 1, 'Rb': 1}))
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        f = chem.EmpiricalFormula(chem.EmpiricalFormula('RaRb'))
        self.assertEqual(f, {'Ra': 1, 'Rb': 1})

        with self.assertRaisesRegex(ValueError, 'not a valid formula'):
            chem.EmpiricalFormula('Hee2')

        with self.assertRaisesRegex(ValueError, 'not a valid formula'):
            chem.EmpiricalFormula('h2')

    def test_EmpiricalFormula_get_attr(self):
        f = chem.EmpiricalFormula()
        self.assertEqual(f.C, 0)
        self.assertEqual(f['C'], 0)

    def test_EmpiricalFormula___setitem__(self):
        f = chem.EmpiricalFormula()
        f.C = 0
        self.assertEqual(f, {})
        self.assertEqual(dict(f), {})
        self.assertEqual(str(f), '')

        f = chem.EmpiricalFormula()
        f.A = 1
        self.assertEqual(f, {'A': 1})
        f.A = 0
        self.assertEqual(f, {})
        self.assertEqual(dict(f), {})
        self.assertEqual(str(f), '')
        f.A = 1.5
        self.assertEqual(f, {'A': 1.5})

        f = chem.EmpiricalFormula()
        with self.assertRaisesRegex(ValueError, 'Coefficient must be a float'):
            f.A = 'a'

        f = chem.EmpiricalFormula()
        with self.assertRaisesRegex(ValueError, 'Element must be a one or two letter string'):
            f.Aaa = 1

    def test_EmpiricalFormula_get_molecular_weight(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertAlmostEqual(f.get_molecular_weight(), 18.015)

    def test_EmpiricalFormula___add__(self):
        f = chem.EmpiricalFormula('H2O')
        g = chem.EmpiricalFormula('HO')
        self.assertEqual(str(f + g), 'H3O2')
        self.assertEqual(str(f + 'HO'), 'H3O2')

    def test_EmpiricalFormula___sub__(self):
        f = chem.EmpiricalFormula('H2O')
        g = chem.EmpiricalFormula('HO')
        self.assertEqual(str(f - g), 'H')
        self.assertEqual(str(f - 'HO'), 'H')

    def test_EmpiricalFormula___mul__(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertEqual(str(f * 2), 'H4O2')

    def test_EmpiricalFormula___truediv__(self):
        f = chem.EmpiricalFormula('H4O2')
        self.assertEqual(f / 2, chem.EmpiricalFormula({'H': 2, 'O': 1}))

    def test_EmpiricalFormula___str__(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertEqual(str(f), 'H2O')

        f = chem.EmpiricalFormula('OH2')
        self.assertEqual(str(f), 'H2O')

        f = chem.EmpiricalFormula('N0OH2')
        self.assertEqual(str(f), 'H2O')

        f = chem.EmpiricalFormula('H2O1.1')
        self.assertEqual(str(f), 'H2O1.1')

        f = chem.EmpiricalFormula('H2O1.1e-3')
        self.assertEqual(str(f), 'H2O0.0011')

        f = chem.EmpiricalFormula('H2O1.1e+3')
        self.assertEqual(str(f), 'H2O1100')

        f = chem.EmpiricalFormula('H2O-1.1e+3')
        self.assertEqual(str(f), 'H2O-1100')

    def test_EmpiricalFormula___contains__(self):
        f = chem.EmpiricalFormula('H2O')
        self.assertIn('H', f)
        self.assertIn('C', f)
        self.assertNotIn('Ccc', f)

    def test_EmpiricalFormula___hash__(self):
        f = chem.EmpiricalFormula('H2O')
        g = chem.EmpiricalFormula('H2O')
        h = chem.EmpiricalFormula('H')

        self.assertIn(f, [g])
        self.assertIn(f, set([g]))
        self.assertIn(f, {g: True})

        self.assertNotIn(f, [h])
        self.assertNotIn(f, set([h]))
        self.assertNotIn(f, {h: True})


class GetMajorMicroSpeciesTestCase(unittest.TestCase):
    ALA = 'InChI=1S/C3H7NO2/c1-2(4)3(5)6/h2H,4H2,1H3,(H,5,6)/t2-/m0/s1'
    GLY = 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)'

    ALA_smiles = 'CC([N+])C([O-])=O'
    GLY_smiles = 'C([N+])C([O-])=O'

    ALA_cml = """<?xml version="1.0" encoding="UTF-8"?>
                 <cml>
                     <molecule id="m1">
                         <atomArray>
                             <atom id="a1" elementType="C" x2="1.5399999999999987" y2="2.667358243656071"></atom>
                             <atom id="a2" elementType="C" x2="2.3099999999999996" y2="1.3336791218280357"></atom>
                             <atom id="a3" elementType="C" x2="1.540000000000000" y2="0.000000000000000"></atom>
                             <atom id="a4" elementType="N" x2="3.8499999999999996" y2="1.3336791218280368"></atom>
                             <atom id="a5" elementType="O" x2="2.3100000000000005" y2="-1.3336791218280353"></atom>
                             <atom id="a6" elementType="O" x2="0.000000000000000" y2="0.000000000000000"></atom>
                         </atomArray>
                         <bondArray>
                             <bond id="b1" atomRefs2="a2 a1" order="1"></bond>
                             <bond id="b2" atomRefs2="a3 a2" order="1"></bond>
                             <bond id="b3" atomRefs2="a4 a2" order="1"></bond>
                             <bond id="b4" atomRefs2="a5 a3" order="2"></bond>
                             <bond id="b5" atomRefs2="a6 a3" order="1"></bond>
                         </bondArray>
                     </molecule>
                 </cml>"""
    ALA_cml_2 = """<molecule id="m1">
                       <atomArray>
                           <atom id="a1" elementType="C" x2="1.5399999999999987" y2="2.667358243656071"></atom>
                           <atom id="a2" elementType="C" x2="2.3099999999999996" y2="1.3336791218280357"></atom>
                           <atom id="a3" elementType="C" x2="1.540000000000000" y2="0.000000000000000"></atom>
                           <atom id="a4" elementType="N" x2="3.8499999999999996" y2="1.3336791218280368"></atom>
                           <atom id="a5" elementType="O" x2="2.3100000000000005" y2="-1.3336791218280353"></atom>
                           <atom id="a6" elementType="O" x2="0.000000000000000" y2="0.000000000000000"></atom>
                       </atomArray>
                       <bondArray>
                           <bond id="b1" atomRefs2="a2 a1" order="1"></bond>
                           <bond id="b2" atomRefs2="a3 a2" order="1"></bond>
                           <bond id="b3" atomRefs2="a4 a2" order="1"></bond>
                           <bond id="b4" atomRefs2="a5 a3" order="2"></bond>
                           <bond id="b5" atomRefs2="a6 a3" order="1"></bond>
                       </bondArray>
                   </molecule>"""

    def test_inchi(self):
        self.assertEqual(marvin.get_major_micro_species(self.GLY, 'inchi', 'inchi', ph=2.), 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p+1')
        self.assertEqual(marvin.get_major_micro_species(self.GLY, 'inchi', 'inchi', ph=13.),
                         'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p-1')
        self.assertEqual(marvin.get_major_micro_species(self.ALA, 'inchi', 'inchi', ph=13.),
                         'InChI=1S/C3H7NO2/c1-2(4)3(5)6/h2H,4H2,1H3,(H,5,6)/p-1/t2-/m0/s1')
        self.assertEqual(marvin.get_major_micro_species([self.ALA, self.GLY], 'inchi', 'inchi', ph=13.), [
            'InChI=1S/C3H7NO2/c1-2(4)3(5)6/h2H,4H2,1H3,(H,5,6)/p-1/t2-/m0/s1',
            'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p-1',
        ])
        self.assertEqual(marvin.get_major_micro_species([self.GLY, self.GLY], 'inchi', 'inchi', ph=13.), [
            'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p-1',
            'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p-1',
        ])

    def test_smiles(self):
        self.assertEqual(marvin.get_major_micro_species(self.GLY_smiles, 'smiles', 'smiles', ph=2.),
                         '[N+]CC(O)=O')
        self.assertEqual(marvin.get_major_micro_species(self.GLY_smiles, 'smiles', 'smiles', ph=13.),
                         '[N+]CC([O-])=O')
        self.assertEqual(marvin.get_major_micro_species(self.ALA_smiles, 'smiles', 'smiles', ph=13.),
                         'CC([N+])C([O-])=O')
        self.assertEqual(marvin.get_major_micro_species([self.ALA_smiles, self.GLY_smiles], 'smiles', 'smiles', ph=13.), [
            'CC([N+])C([O-])=O',
            '[N+]CC([O-])=O',
        ])
        self.assertEqual(marvin.get_major_micro_species([self.GLY_smiles, self.GLY_smiles], 'smiles', 'smiles', ph=13.), [
            '[N+]CC([O-])=O',
            '[N+]CC([O-])=O',
        ])

    def test_cml(self):
        result = marvin.get_major_micro_species(self.ALA_cml, 'cml', 'cml', ph=2.)
        self.assertTrue(result.startswith('<?xml'))

        result = marvin.get_major_micro_species(self.ALA_cml_2, 'cml', 'cml', ph=2.)
        self.assertTrue(result.startswith('<?xml'))

    def test_errors(self):
        import jnius
        with self.assertRaises(jnius.JavaException):
            marvin.get_major_micro_species('C2H5NO2', 'inchi', 'inchi', ph=2.)


class DrawMoleculeTestCase(unittest.TestCase):
    ALA = 'InChI=1S/C3H7NO2/c1-2(4)3(5)6/h2H,4H2,1H3,(H,5,6)/t2-/m0/s1'

    def test(self):
        svg = marvin.draw_molecule(self.ALA, 'inchi',
                                 atom_labels=[
                                     {'position': 1, 'element': 'C', 'label': 'A', 'color': 0xff0000},
                                     {'position': 2, 'element': 'C', 'label': 'B', 'color': 0x00ff00},
                                     {'position': 3, 'element': 'C', 'label': 'C', 'color': 0x0000ff},
                                 ],
                                 atom_sets=[
                                     {'positions': [1], 'elements': ['C'], 'color': 0xff0000},
                                     {'positions': [2], 'elements': ['C'], 'color': 0x00ff00},
                                     {'positions': [3], 'elements': ['C'], 'color': 0x0000ff},
                                 ],
                                 bond_sets=[
                                     {'positions': [[2, 3], [3, 5]], 'elements': [['C', 'C'], ['C', 'O']], 'color': 0xff00ff},
                                     {'positions': [[3, 6]], 'elements': [['C', 'O']], 'color': 0xffff00},
                                 ])
        self.assertTrue(svg.startswith('<?xml'))
        self.assertIn('#ff00ff', svg)
        self.assertIn('#ffff00', svg)

        svg = marvin.draw_molecule(self.ALA, 'inchi', atom_labels=[
            {'position': 1, 'element': 'C', 'label': 'A', 'color': 0xff0000},
            {'position': 2, 'element': 'C', 'label': 'B', 'color': 0x00ff00},
            {'position': 3, 'element': 'C', 'label': 'C', 'color': 0x0000ff},
        ],
            atom_sets=[
            {'positions': [1], 'elements': ['C'], 'color': 0xff0000},
            {'positions': [2], 'elements': ['C'], 'color': 0x00ff00},
            {'positions': [3], 'elements': ['C'], 'color': 0x0000ff},
        ], show_atom_nums=True, include_xml_header=False)
        self.assertTrue(svg.startswith('<svg'))

        svg = marvin.draw_molecule(self.ALA, 'inchi')

        file, filename = tempfile.mkstemp()
        os.close(file)
        with open(filename, 'wb') as file:
            file.write(marvin.draw_molecule(self.ALA, 'inchi', image_format='png'))
        self.assertEqual(imghdr.what(filename), 'png')
        os.remove(filename)


class OpenBabelUtilsTestCase(unittest.TestCase):
    def test_get_formula(self):
        gly_inchi = 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)'
        gly_formula = 'C2H5NO2'
        mol = openbabel.OBMol()
        conversion = openbabel.OBConversion()
        conversion.SetInFormat('inchi')
        conversion.ReadString(mol, gly_inchi)
        self.assertEqual(chem.OpenBabelUtils.get_formula(mol), chem.EmpiricalFormula('C2H5NO2'))

    def test_get_inchi(self):
        gly_inchi = 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)'
        mol = openbabel.OBMol()
        conversion = openbabel.OBConversion()
        conversion.SetInFormat('inchi')
        conversion.ReadString(mol, gly_inchi)
        self.assertEqual(chem.OpenBabelUtils.get_inchi(mol), gly_inchi)

    def test_export(self):
        gly_smiles = 'C([N+])C([O-])=O'
        mol = openbabel.OBMol()
        conversion = openbabel.OBConversion()
        conversion.SetInFormat('can')
        conversion.ReadString(mol, gly_smiles)
        self.assertEqual(chem.OpenBabelUtils.export(mol, 'smi'), 'C([N+])C(=O)[O-]')
        self.assertEqual(chem.OpenBabelUtils.export(mol, 'smi', options=('c',)), '[O-]C(=O)C[N+]')

        gly_inchi = 'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)'
        mol = openbabel.OBMol()
        conversion = openbabel.OBConversion()
        conversion.SetInFormat('inchi')
        conversion.ReadString(mol, gly_inchi)
        self.assertEqual(chem.OpenBabelUtils.export(mol, 'inchi'), gly_inchi)

        self.assertTrue(chem.OpenBabelUtils.export(mol, 'mol', options='m').endswith('END'))
