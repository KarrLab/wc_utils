""" Tests of the ontology utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2019-01-14
:Copyright: 2019, Karr Lab
:License: MIT
"""

import pronto
import unittest
import wc_utils.util.ontology


class OntologyTestCase(unittest.TestCase):
    def test_are_terms_equivalent(self):
        onto1 = pronto.Ontology()
        onto2 = pronto.Ontology()

        term1_a = onto1.create_term(id='term_a')
        term1_b = onto1.create_term(id='term_b')
        term2_a = onto2.create_term(id='term_a')

        self.assertEqual(term1_a, term1_a)
        self.assertEqual(term1_b, term1_b)
        self.assertNotEqual(term1_a, term1_b)

        self.assertTrue(term1_a == term1_a)
        self.assertTrue(term1_b == term1_b)
        self.assertFalse(term1_a == term1_b)

        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term1_a, term1_a))
        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term1_b, term1_b))
        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term2_a, term2_a))
        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term1_a, term2_a))
        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term2_a, term1_a))
        self.assertFalse(wc_utils.util.ontology.are_terms_equivalent(term1_a, term1_b))
        self.assertFalse(wc_utils.util.ontology.are_terms_equivalent(term1_b, term1_a))
        self.assertFalse(wc_utils.util.ontology.are_terms_equivalent(term2_a, term1_b))
        self.assertFalse(wc_utils.util.ontology.are_terms_equivalent(term1_b, term2_a))
