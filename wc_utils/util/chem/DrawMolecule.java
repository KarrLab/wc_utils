import chemaxon.formats.MolExporter;
import chemaxon.marvin.io.formats.MoleculeImporter;
import chemaxon.struc.MDocument;
import chemaxon.struc.MolAtom;
import chemaxon.struc.Molecule;
import java.awt.Color;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import chemaxon.marvin.io.formats.vectgraphics.SvgExporter;

/**
 * Draw a molecule.
 *
 * @date 2019-03-05
 * @author Jonathan Karr <karr@mssm.edu>
 */
public class DrawMolecule {
    /* Draw a molecule.
     */
     public static String run_one(String inStructure, String inStructureFormat,
        int[] atomsToLabel, String[] atomLabels, int[] atomLabelColors,
        int[][] atomSets, int[] atomSetColors) throws IOException {
        // read from string (e.g., "inchi", "smiles")
        ByteArrayInputStream inStream = new ByteArrayInputStream(inStructure.getBytes());
        MoleculeImporter molImporter = new MoleculeImporter(inStream, inStructureFormat);
        Molecule inMol = molImporter.read();

        MDocument mdoc = new MDocument(inMol);
        Color green = new Color(0, 255, 0);

        // set atom labels
        MolAtom atom;
        for (int iLabel = 0; iLabel < atomsToLabel.length; iLabel++) {
            atom = inMol.getAtom(atomsToLabel[iLabel] - 1);
            atom.setExtraLabel(atomLabels[iLabel]);
            atom.setExtraLabelColor(atomLabelColors[iLabel]);
        }
        for (int iSet = 0; iSet < atomSets.length; iSet++) {
            for (int iAtom = 0; iAtom < atomSets[iSet].length; iAtom++) {
                atom = inMol.getAtom(atomSets[iSet][iAtom] - 1);
                atom.setSetSeq(iSet + 1);
            }

            mdoc.setAtomSetColorMode(iSet + 1, MDocument.SETCOLOR_SPECIFIED);
            mdoc.setAtomSetRGB(iSet + 1, atomSetColors[iSet]);
        }

        // write to string
        ByteArrayOutputStream outStream = new ByteArrayOutputStream();
        String image = (String)MolExporter.exportToObject(inMol, "svg:mono,anum");

        // return image
        return image;
    }
}
