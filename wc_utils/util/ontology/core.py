""" Ontology utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2019-01-14
:Copyright: 2019, Karr Lab
:License: MIT
"""

import os.path
import pkg_resources
import pronto

wcm_ontology = pronto.Ontology(pkg_resources.resource_filename(
    'wc_utils', os.path.join('util', 'ontology', 'WCM.obo')))
# :obj:`pronto.Ontology`: whole-cell modeling ontology
