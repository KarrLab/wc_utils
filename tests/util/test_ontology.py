""" Tests of the ontology utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2019-01-14
:Copyright: 2019, Karr Lab
:License: MIT
"""

import os
import pkg_resources
import pronto
import unittest
import wc_utils.util.ontology


class OntologyTestCase(unittest.TestCase):
    def test_are_terms_equivalent(self):
        onto1 = pronto.Ontology(pkg_resources.resource_filename(
            'wc_onto', os.path.join('onto.obo')))
        onto2 = pronto.Ontology(pkg_resources.resource_filename(
            'wc_onto', os.path.join('onto.obo')))

        wc_utils.util.ontology.are_terms_equivalent(onto1['WC:representation'], onto1['WC:representation'])
        wc_utils.util.ontology.are_terms_equivalent(onto1['WC:representation'], onto2['WC:representation'])
        wc_utils.util.ontology.are_terms_equivalent(onto2['WC:representation'], onto1['WC:representation'])
