import chemaxon.formats.MolExporter;
import chemaxon.marvin.calculations.MajorMicrospeciesPlugin;
import chemaxon.marvin.io.formats.MoleculeImporter;
import chemaxon.marvin.plugin.PluginException;
import chemaxon.struc.Molecule;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

/**
 * Reads a molecule from InChI, calculate the major protonation state, and
 * writes the molecule to InChI.
 *
 * @date 2019-02-11
 * @author Jonathan Karr <karr@mssm.edu>
 */
public class Protonator {
    /* Reads a molecule from InChI, calculate the major protonation state, and
     * writes the molecule to InChI.
     */
    public static String run_one(String inInchi, Float ph, boolean majorTautomer, boolean keepExplicitHydrogens) throws IOException, PluginException {
        // read from InChI
        ByteArrayInputStream inStream = new ByteArrayInputStream(inInchi.getBytes());
        MoleculeImporter molImporter = new MoleculeImporter(inStream, "inchi");
        Molecule inMol = molImporter.read();

        // protonate
        MajorMicrospeciesPlugin plugin = new MajorMicrospeciesPlugin();
        plugin.setpH(ph);
        plugin.setTakeMajorTatomericForm(majorTautomer);
        plugin.setKeepExplicitHydrogens(keepExplicitHydrogens);
        plugin.setMolecule(inMol);
        plugin.run();
        Molecule outMol = plugin.getMajorMicrospecies();

        // write to InChI
        ByteArrayOutputStream outStream = new ByteArrayOutputStream();
        MolExporter molExporter = new MolExporter(outStream, "inchi");
        molExporter.write(outMol);
        String outInchi = outStream.toString();

        // strip extra formatting from InChI
        int i_line = outInchi.indexOf("\n");
        if (i_line > -1)
           outInchi = outInchi.substring(0, outInchi.indexOf("\n"));
       
        // return InChI
        return outInchi;
    }

    public static String[] run_multiple(String[] inInchi, Float ph, boolean majorTautomer, boolean keepExplicitHydrogens) throws IOException, PluginException {
        // read from InChI
        String[] outInchi = new String[inInchi.length];
        for (int i = 0; i < inInchi.length; i++) {
            outInchi[i] = Protonator.run_one(inInchi[i], ph, majorTautomer, keepExplicitHydrogens);
        }
        return outInchi;
    }
}