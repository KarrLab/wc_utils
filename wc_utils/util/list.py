""" List utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-30
:Copyright: 2016, Karr Lab
:License: MIT
"""


def is_sorted(lst, le_cmp=None):
    """ Check if a list is sorted

    Args:
        lst (:obj:`list`): list to check
        le_cmp (:obj:`function`, optional): less than equals comparison function

    Returns
        :obj:`bool`: true if the list is sorted
    """
    if le_cmp:
        return all(le_cmp(a, b) for a, b in zip(lst[:-1], lst[1:]))
    return all(a <= b for a, b in zip(lst[:-1], lst[1:]))


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
