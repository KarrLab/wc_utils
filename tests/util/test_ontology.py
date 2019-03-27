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
        term1_a = pronto.Term(id='term1')
        term1_b = pronto.Term(id='term1')
        term2 = pronto.Term(id='term2')
        self.assertFalse(term1_a == term1_b)
        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term1_a, term1_b))
        self.assertTrue(wc_utils.util.ontology.are_terms_equivalent(term1_b, term1_a))
        self.assertFalse(wc_utils.util.ontology.are_terms_equivalent(term1_a, term2))
        self.assertFalse(wc_utils.util.ontology.are_terms_equivalent(term2, term1_a))
