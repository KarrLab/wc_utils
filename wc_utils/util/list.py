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


def det_find_dupes(l):
    """ Deterministically find dupes in an iterable

    Returns the duplicates in `l`. That is, returns a new list that contains one instance of
    each element that has multiple copies in `l` and orders these instances by their first occurrence in `l`.
    Costs O(n), where n is the length of `l`.

    Args:
        l (:obj:`list`): a list with hashable elements

    Returns:
        :obj:`list`: a deterministically deduplicated copy of `l`

    Raises:
        `TypeError` if an element of `l` is an unhashable (mutable) type
    """
    counts_to_2 = {}
    dupes = []
    for e in l:
        if e not in counts_to_2:
            counts_to_2[e] = 1
        elif counts_to_2[e] == 1:
            counts_to_2[e] += 1
            dupes.append(e)
    return dupes


def get_count_limited_class(classes, class_name, min=1, max=1):
    """ Find a class in an iterator over classes, and constrain its count

    Args:
        classes (:obj:`iterator`): an iterator over some classes
        class_name (:obj:`str`): the desired class' name
        min (:obj:`int`): the fewest instances of a class named `class_name` allowed
        max (:obj:`int`): the most instances of a class named `class_name` allowed

    Returns:
        :obj:`type`: the class in `classes` whose name (`__name__`) is `class_name`; if no instances
            of class are allowed, and no instances are found in `classes`, then return `None`

    Raises:
        :obj:`ValueError`: if `min` > `max, or
            if `classes` doesn't contain between `min` and `max`, inclusive, class(es)
                whose name is `class_name`, or
            if `classes` contains multiple, distinct classes with the name `class_name`
    """
    if min > max:
        raise ValueError("min ({}) > max ({})".format(min, max))
    matching_classes = [cls for cls in classes if cls.__name__ == class_name]
    if len(matching_classes) < min or max < len(matching_classes):
        raise ValueError("the number of members of 'classes' named '{}' must be in [{}, {}], but it is {}".format(
            class_name, min, max, len(matching_classes)))
    # confirm that all elements in matching_classes are the same
    unique_matching_classes = set(matching_classes)
    if 1 < len(unique_matching_classes):
        raise ValueError("'classes' should contain at most 1 class named '{}', but it contains {}".format(
            class_name, len(unique_matching_classes)))
    if matching_classes:
        return matching_classes[0]
    return None


def det_count_elements(l):
    """ Deterministically count elements in an iterable

    Returns the count of each element in `l`. Costs O(n), where n is the length of `l`.

    Args:
        l (:obj:`iterable`): an iterable with hashable elements

    Returns:
        :obj:`list` of :obj:`tuple`: a list of pairs, (element, count), for each element in `l`

    Raises:
        `TypeError` if an element of `l` is an unhashable (mutable) type
    """
    counts = {}
    found = []
    for e in l:
        if e not in counts:
            counts[e] = 0
            found.append(e)
        counts[e] += 1
    return [(e, counts[e]) for e in found]


def elements_to_str(l):
    """ Convert each element in an iterator to a string representation

    Args:
        l (:obj:`list`): an iterator

    Returns:
        :obj:`list`: a list containing each element of the iterator converted to a string
    """
    return [str(e) for e in l]


def dict_by_class(obj_list):
    """ Create a `dict` keyed by class from a list of objects

    Args:
        obj_list (:obj:`list`) list of objects

    Returns:
        :obj:`dict`: mapping from object class to list of objects of that class
    """
    obj_dict = {}
    for obj in obj_list:
        cls = obj.__class__
        if cls not in obj_dict:
            obj_dict[cls] = []
        obj_dict[cls].append(obj)
    return obj_dict
