""" Tests of the chemistry utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_utils.util.chem import marvin
import imghdr
import os
import tempfile
import unittest


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
        self.assertEqual(marvin.get_major_micro_species(self.GLY, 'inchi', 'inchi', ph=2.),
                         'InChI=1S/C2H5NO2/c3-1-2(4)5/h1,3H2,(H,4,5)/p+1')
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
