import chemaxon.formats.MolExporter;
import chemaxon.marvin.io.formats.MoleculeImporter;
import chemaxon.struc.MDocument;
import chemaxon.struc.MolAtom;
import chemaxon.struc.MolBond;
import chemaxon.struc.Molecule;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

/**
 * Draw a molecule.
 *
 * @date 2019-03-05
 * @author Jonathan Karr <karr@mssm.edu>
 */
public class DrawMolecule {
    /* Draw a molecule.
     */
     public static java.lang.Object run(String inStructure, String inStructureFormat, String outImageFormat,
        int[] atomsToLabel, String[] atomElements, String[] atomLabels, int[] atomLabelColors,
        int[][] atomSets, String[][] atomSetElements, int[] atomSetColors, 
        int[][][] bondSets, String[][][] bondSetElements, int[] bondSetColors, 
        boolean showAtomNums,
        int width, int height, boolean includeXmlHeader)
        throws IOException {
        // read from string (e.g., "inchi", "smiles")
        ByteArrayInputStream inStream = new ByteArrayInputStream(inStructure.getBytes());
        MoleculeImporter molImporter = new MoleculeImporter(inStream, inStructureFormat);
        Molecule inMol = molImporter.read();

        // set atom labels and colors
        MolAtom atom;
        for (int iLabel = 0; iLabel < atomsToLabel.length; iLabel++) {
            if (atomsToLabel[iLabel] <= inMol.getAtomCount()) {
                atom = inMol.getAtom(atomsToLabel[iLabel] - 1);
                if (atom.getSymbol().equals(atomElements[iLabel])) {
                    atom.setExtraLabel(atomLabels[iLabel]);
                    atom.setExtraLabelColor(atomLabelColors[iLabel]);
                }
            }
        }

        MDocument mdoc = new MDocument(inMol);
        for (int iSet = 0; iSet < atomSetColors.length; iSet++) {
            for (int iAtom = 0; iAtom < atomSets[iSet].length; iAtom++) {
                if (atomSets[iSet][iAtom] <= inMol.getAtomCount()) {
                    atom = inMol.getAtom(atomSets[iSet][iAtom] - 1);
                    if (atom.getSymbol().equals(atomSetElements[iSet][iAtom])) {
                        atom.setSetSeq(iSet + 1);
                    }
                }
            }

            mdoc.setAtomSetColorMode(iSet + 1, MDocument.SETCOLOR_SPECIFIED);
            mdoc.setAtomSetRGB(iSet + 1, atomSetColors[iSet]);
        }

        // set bond colors
        MolBond bond;
        MolAtom atom_1;
        MolAtom atom_2;
        for (int iSet = 0; iSet < bondSetColors.length; iSet++) {
            for (int iBond = 0; iBond < bondSets[iSet].length; iBond++) {
                if (bondSets[iSet][iBond][0] <= inMol.getAtomCount() && 
                    bondSets[iSet][iBond][1] <= inMol.getAtomCount()) {
                    atom_1 = inMol.getAtom(bondSets[iSet][iBond][0] - 1);
                    atom_2 = inMol.getAtom(bondSets[iSet][iBond][1] - 1);
                    bond = atom_1.getBondTo(atom_2);
                    if (atom_1.getSymbol().equals(bondSetElements[iSet][iBond][0]) &&
                        atom_2.getSymbol().equals(bondSetElements[iSet][iBond][1]) &&
                        bond != null) {
                        bond.setSetSeq(iSet + 1);
                    }
                }
            }

            mdoc.setBondSetColorMode(iSet + 1, MDocument.SETCOLOR_SPECIFIED);
            mdoc.setBondSetRGB(iSet + 1, bondSetColors[iSet]);
        }

        // write to string
        ByteArrayOutputStream outStream = new ByteArrayOutputStream();
        String format = outImageFormat + ":mono,#00ffffff,transbg,maxscale1000,marginSize0";
        if (showAtomNums) {
            format += ",anum";
        }
        format += ",w" + Integer.toString(width);
        format += ",h" + Integer.toString(height);
        if (!includeXmlHeader && outImageFormat.equals("svg")) {
            format += ",headless";
        }
        java.lang.Object image = (java.lang.Object)MolExporter.exportToObject(inMol, format);

        // return image
        return image;
    }
}
