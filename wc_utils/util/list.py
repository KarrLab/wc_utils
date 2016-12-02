""" List utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-30
:Copyright: 2016, Karr Lab
:License: MIT
"""


def transpose(lst):
    """ Swaps the first two dimensions of a two (or more) dimensional list

    Args:
        lst (:obj:`list` of `list`): two-dimensional list

    Returns:
        :obj:`list` of `list`: two-dimensional list
    """
    t_lst = []
    for i_row, row in enumerate(lst):
        for i_col, value in enumerate(row):
            if i_col >= len(t_lst):
                t_lst.append([])
            t_lst[i_col].append(value)

    return t_lst
