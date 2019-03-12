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
from wc_utils.util import ontology


class OntologyTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(ontology.wcm_ontology, pronto.Ontology)
        self.assertIsInstance(ontology.wcm_ontology['WCM:representation'], pronto.term.Term)

    def test_are_terms_equivalent(self):
        onto1 = pronto.Ontology(pkg_resources.resource_filename(
            'wc_utils', os.path.join('util', 'ontology', 'WCM.obo')))
        onto2 = pronto.Ontology(pkg_resources.resource_filename(
            'wc_utils', os.path.join('util', 'ontology', 'WCM.obo')))

        ontology.are_terms_equivalent(onto1['WCM:representation'], onto1['WCM:representation'])
        ontology.are_terms_equivalent(onto1['WCM:representation'], onto2['WCM:representation'])
        ontology.are_terms_equivalent(onto2['WCM:representation'], onto1['WCM:representation'])
