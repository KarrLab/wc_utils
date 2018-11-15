""" List utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-30
:Copyright: 2016-2018, Karr Lab
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
        lst (:obj:`list` of :obj:`list`): two-dimensional list

    Returns:
        :obj:`list` of :obj:`list`: two-dimensional list
    """
    t_lst = []
    for i_row, row in enumerate(lst):
        for i_col, value in enumerate(row):
            if i_col >= len(t_lst):
                t_lst.append([])
            t_lst[i_col].append(value)

    return t_lst


def difference(list_1, list_2):
    """ Deterministically find the difference between two lists

    Returns the elements in `list_1` that are not in `list_2`. Behaves deterministically, whereas
    set difference does not. Computational cost is O(max(l1, l2)), where l1 and l2 are len(list_1)
    and len(list_2), respectively.

    Args:
        list_1 (:obj:`list`): one-dimensional list
        list_2 (:obj:`list`): one-dimensional list

    Returns:
        :obj:`list`: a set-like difference between `list_1` and `list_2`

    Raises:
        `TypeError` if `list_1` or `list_2` contains an unhashable (mutable) type
    """
    list_2_set = set(list_2)
    return list(filter(lambda item:not item in list_2_set, list_1))


def det_dedupe(l):
    """ Deterministically deduplicate a list

    Returns a deduplicated copy of `l`. That is, returns a new list that contains one instance of
    each element in `l` and orders these instances by their first occurrence in `l`.
    Costs O(n), where n is the length of `l`.

    Args:
        l (:obj:`list`): a list with hashable elements

    Returns:
        :obj:`list`: a deterministically deduplicated copy of `l`

    Raises:
        `TypeError` if `l` contains an unhashable (mutable) type
    """
    s = set()
    t = []
    for e in l:
        if e not in s:
            t.append(e)
            s.add(e)
    return t

def elements_to_str(l):
    """ Convert each element in an iterator to a string representation

    Args:
        l (:obj:`list`): an iterator

    Returns:
        :obj:`list`: a list containing each element of the iterator converted to a string
    """
    return [str(e) for e in l]
