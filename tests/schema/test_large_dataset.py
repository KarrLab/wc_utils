""" Large test case

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-03-23
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils.schema import core
from wc_utils.schema import utils
from wc_utils.util.list import is_sorted
import sys
import unittest


class Model(core.Model):
    id = core.SlugAttribute()


class Gene(core.Model):
    model = core.ManyToOneAttribute(Model, related_name='genes')
    id = core.SlugAttribute()


class Rna(core.Model):
    model = core.ManyToOneAttribute(Model, related_name='rna')
    gene = core.ManyToOneAttribute(Gene, related_name='rna')
    id = core.SlugAttribute()


class Protein(core.Model):
    model = core.ManyToOneAttribute(Model, related_name='proteins')
    rna = core.ManyToOneAttribute(Rna, related_name='proteins')
    id = core.SlugAttribute()


class Metabolite(core.Model):
    model = core.ManyToOneAttribute(Model, related_name='metabolites')
    id = core.SlugAttribute()


class Reaction(core.Model):
    model = core.ManyToOneAttribute(Model, related_name='reactions')
    id = core.SlugAttribute()
    metabolites = core.ManyToManyAttribute(Metabolite, related_name='reactions')
    enzyme = core.ManyToOneAttribute(Protein, related_name='reactions')


def generate_model(n_gene, n_rna, n_prot, n_met):
    model = Model(id='model')

    for i_gene in range(1, n_gene + 1):
        gene = model.genes.create(id='Gene_{}'.format(i_gene))
        for i_rna in range(1, n_rna + 1):
            rna = model.rna.create(id='Rna_{}_{}'.format(i_gene, i_rna), gene=gene)
            for i_prot in range(1, n_prot + 1):
                prot = model.proteins.create(id='Protein_{}_{}_{}'.format(i_gene, i_rna, i_prot), rna=rna)

    for i_met in range(1, n_met + 1):
        met = model.metabolites.create(id='Metabolite_{}'.format(i_met))

    prots = Protein.sort(model.proteins)
    mets = Metabolite.sort(model.metabolites)
    for i_rxn in range(1, n_gene * n_rna * n_prot + 1):
        rxn = model.reactions.create(id='Reaction_{}'.format(i_rxn), enzyme=prots[i_rxn - 1], metabolites=[
            mets[(i_rxn - 1 + 0) % n_met],
            mets[(i_rxn - 1 + 1) % n_met],
            mets[(i_rxn - 1 + 2) % n_met],
            mets[(i_rxn - 1 + 3) % n_met],
        ])

    return model


class TestMediumDataset(unittest.TestCase):
    """ Test that the methods work on reasonably sized datasets """

    n_gene = 50
    n_rna = 2
    n_prot = 2
    n_met = 50

    def setUp(self):
        self.regular_recursion_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(100)

    def tearDown(self):
        sys.setrecursionlimit(self.regular_recursion_limit)

    def test_get_related(self):
        model = generate_model(self.n_gene, self.n_rna, self.n_prot, self.n_met)
        objects = model.get_related()
        self.assertEqual(len(objects), 1 + self.n_gene + self.n_gene * self.n_rna +
                         2 * self.n_gene * self.n_rna * self.n_prot + self.n_met)

    def test_normalize(self):
        model = generate_model(self.n_gene, self.n_rna, self.n_prot, self.n_met)
        utils.randomize_object_graph(model)
        model.normalize()

        self.assertTrue(is_sorted([gene.id for gene in model.genes]))
        self.assertTrue(is_sorted([rna.id for rna in model.rna]))
        self.assertTrue(is_sorted([prot.id for prot in model.proteins]))
        self.assertTrue(is_sorted([met.id for met in model.metabolites]))
        self.assertTrue(is_sorted([rxn.id for rxn in model.reactions]))

        for met in model.metabolites:
            self.assertTrue(is_sorted([rxn.id for rxn in met.reactions]))

        for prot in model.proteins:
            self.assertTrue(is_sorted([rxn.id for rxn in prot.reactions]))

        for rxn in model.reactions:
            self.assertTrue(is_sorted([met.id for met in rxn.metabolites]))

    @unittest.skip('get me working')
    def test_eq(self):
        model = generate_model(self.n_gene, self.n_rna, self.n_prot, self.n_met)
        model2 = generate_model(self.n_gene, self.n_rna, self.n_prot, self.n_met)
        self.assertTrue(model2.is_equal(model))

    @unittest.skip('implement me')
    def test_difference(self):
        pass

    @unittest.skip('implement me')
    def test_validate(self):
        pass

    @unittest.skip('implement me')
    def test_read_write(self):
        pass


@unittest.skip("Skipping because test is long")
class TestLargeDataset(TestMediumDataset):
    n_gene = 1000
    n_rna = 3
    n_prot = 3
    n_met = 800


@unittest.skip("Skipped because test is long")
class TestHugeDataset(TestMediumDataset):
    n_gene = 30000
    n_rna = 3
    n_prot = 3
    n_met = 8000
