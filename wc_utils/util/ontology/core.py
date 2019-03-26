""" Ontology utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2019-01-14
:Copyright: 2019, Karr Lab
:License: MIT
"""

import pronto


def are_terms_equivalent(term1, term2):
    """ Determine if two terms are semantically equivalent

    Args:
        term1 (:obj:`pronto.Term`): term
        term2 (:obj:`pronto.Term`): other term

    Returns:
        :obj:`bool`: :obj:`True` if the terms are semantically equivalent
    """
    return term1 is term2 or (term1.__class__ == term2.__class__ and term1.id == term2.id)
