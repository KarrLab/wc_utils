""" Tests of the ontology utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2019-01-14
:Copyright: 2019, Karr Lab
:License: MIT
"""

import pronto
import unittest


class OntologyTestCase(unittest.TestCase):
    def test(self):
        from wc_utils.util import ontology
        self.assertIsInstance(ontology.wcm_ontology, pronto.Ontology)
        self.assertIsInstance(ontology.wcm_ontology['WCM:representation'], pronto.term.Term)
