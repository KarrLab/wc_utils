import chemaxon.formats.MolExporter;
import chemaxon.marvin.calculations.MajorMicrospeciesPlugin;
import chemaxon.marvin.io.formats.MoleculeImporter;
import chemaxon.marvin.plugin.PluginException;
import chemaxon.struc.Molecule;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

/**
 * Reads a molecule from strings, calculate the major protonation state, and
 * writes the molecule to strings.
 *
 * @date 2019-02-11
 * @author Jonathan Karr <karr@mssm.edu>
 */
public class GetMajorMicroSpecies {
    /* Reads a molecule from a string (e.g., InChI, SMILES), calculate the major protonation state, and
     * writes the molecule to a string (e.g., InChI, SMILES).
     */
    public static String run_one(String inStructure, String inStructureFormat, String outStructureFormat,
        Float ph, boolean majorTautomer, boolean keepExplicitHydrogens) throws IOException, PluginException {
        // read from string (e.g., "inchi", "smiles")
        ByteArrayInputStream inStream = new ByteArrayInputStream(inStructure.getBytes());
        MoleculeImporter molImporter = new MoleculeImporter(inStream, inStructureFormat);
        Molecule inMol = molImporter.read();

        // dearomatize
        inMol.dearomatize();

        // protonate
        MajorMicrospeciesPlugin plugin = new MajorMicrospeciesPlugin();
        plugin.setpH(ph);
        plugin.setTakeMajorTatomericForm(majorTautomer);
        plugin.setKeepExplicitHydrogens(keepExplicitHydrogens);
        plugin.setMolecule(inMol);
        plugin.run();
        Molecule outMol = plugin.getMajorMicrospecies();

        // write to string
        ByteArrayOutputStream outStream = new ByteArrayOutputStream();
        MolExporter molExporter = new MolExporter(outStream, outStructureFormat);
        molExporter.write(outMol);
        String outStructure = outStream.toString();

        // return structure
        return outStructure;
    }

    public static String[] run_multiple(String[] inStructures, String inStructureFormat, String outStructureFormat,
        Float ph, boolean majorTautomer, boolean keepExplicitHydrogens) throws IOException, PluginException {
        String[] outStructures = new String[inStructures.length];
        for (int i = 0; i < inStructures.length; i++) {
            outStructures[i] = GetMajorMicroSpecies.run_one(inStructures[i], inStructureFormat, outStructureFormat,
                ph, majorTautomer, keepExplicitHydrogens);
        }
        return outStructures;
    }
}