""" String utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-03-20
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

import collections
import re
import six


def indent_forest(forest, indentation=2, keep_trailing_blank_lines=False, return_list=False):
    """ Generate a string of lines, each indented by its depth in `forest`

    Convert a forest of objects provided in an iterator of nested iterators into a flat list of
    strings, each indented by depth*indentation spaces where depth is the objects' depth in `forest`.

    Strings are not treated as iterators. Properly handles strings containing newlines. Trailing
    blank lines are removed from strings containing newlines.

    Args:
        forest (:obj:`iterators` of `iterators`): a forest as an iterator of nested iterators
        indentation (:obj:`int`, optional): number of spaces to indent at each level
        keep_trailing_blank_lines (:obj:`Boolean`, optional): if set, keep trailing blank lines in
            strings in `forest`
        return_list (:obj:`Boolean`, optional): if set, return a list of lines, each indented by
            its depth in `forest`

    Returns:
        :obj:`str`: a string of lines, each indented by its depth in `forest`
    """
    if return_list:
        return __indent_forest(forest, indentation, depth=0,
                               keep_trailing_blank_lines=keep_trailing_blank_lines)
    else:
        return '\n'.join(__indent_forest(forest, indentation, depth=0,
                                         keep_trailing_blank_lines=keep_trailing_blank_lines))


def __indent_forest(forest, indentation, depth, keep_trailing_blank_lines):
    """ Private, recursive method to generate a list of lines indented by their depth in a forest

    Args:
        forest (:obj:`list` of :obj:`list`): a forest as an iterator of nested iterators
        indentation (:obj:`int`): number of spaces to indent at each level
        depth (:obj:`int`): recursion depth, used by recursion
        keep_trailing_blank_lines (:obj:`Boolean`): if set, keep trailing blank lines in strings in
            `forest`

    Returns:
        :obj:`list` of :obj:`str`: list of strings, appropriately indented
    """
    indent = ' ' * depth * indentation
    output = []
    if _iterable_not_string(forest):
        for entry in forest:
            if _iterable_not_string(entry):
                output += __indent_forest(entry, indentation, depth + 1, keep_trailing_blank_lines)
            else:
                e_str = str(entry)
                if '\n' in e_str:
                    lines = e_str.split('\n')
                    if not keep_trailing_blank_lines:
                        delete_trailing_blanks(lines)
                    for line in lines:
                        output.append(indent + line)
                else:
                    output.append(indent + e_str)
    else:
        output.append(indent + str(forest))
    return output


def _iterable_not_string(o):
    # todo: try to simplify & generalize this by using isinstance(o, basestring)
    return isinstance(o, collections.Iterable) and not isinstance(o, six.string_types)


def delete_trailing_blanks(l_of_strings):
    """ Remove all blank lines from the end of a list of strings

    A line is blank if it is empty after applying `String.rstrip()`.

    Args:
        l_of_strings (:obj:`list` of :obj:`str`): a list of strings
    """
    last = None
    for i, e in reversed(list(enumerate(l_of_strings))):
        e = e.rstrip()
        if e:
            break
        last = i
    if last is not None:
        del l_of_strings[last:]


def find_nth(s, sub, n, start=0, end=float('inf')):
    """ Get the index of the nth occurrence of a substring within a string

    Args:
        s (:obj:`str`): string to search
        sub (:obj:`str`): substring to search for
        n (:obj:`int`): number of occurence to find the position of
        start (:obj:`int`, optional): starting position to search from
        end (:obj:`int`, optional): end position to search within

    Returns:
        :obj:`int`: index of nth occurence of the substring within the string
            or -1 if there are less than n occurrences of the substring within
            the string

    Raises:
        :obj:`ValueError`: if `sub` is empty or `n` is less than 1
    """
    if not sub:
        raise ValueError('sep cannot be empty')
    if n < 1:
        raise ValueError('n must be at least 1')

    L = len(s)
    l = len(sub)
    count = 0
    i = start
    while i < min(end, L) - l + 1:
        if s[i:i+l] == sub:
            count += 1
            if count == n:
                return i
            i += l
        else:
            i += 1

    return -1


def rfind_nth(s, sub, n, start=0, end=float('inf')):
    """ Get the index of the nth-last occurrence of a substring within a string

    Args:
        s (:obj:`str`): string to search
        sub (:obj:`str`): substring to search for
        n (:obj:`int`): number of occurence to find the position of
        start (:obj:`int`, optional): starting position to search from
        end (:obj:`int`, optional): end position to search within

    Returns:
        :obj:`int`: index of nth-last occurence of the substring within the string
            or -1 if there are less than n occurrences of the substring within
            the string

    Raises:
        :obj:`ValueError`: if `sub` is empty or `n` is less than 1
    """
    if not sub:
        raise ValueError('sep cannot be empty')
    if n < 1:
        raise ValueError('n must be at least 1')

    L = len(s)
    l = len(sub)
    count = 0
    i = min(L, end) - l
    while i >= start:
        if s[i:i+l] == sub:
            count += 1
            if count == n:
                return i
            i -= l
        else:
            i -= 1

    return -1


def partition_nth(s, sep, n):
    """ Partition a string on the nth occurrence of a substring

    Args:
        s (:obj:`str`): string to partition
        sep (:obj:`str`): separator to partition on
        n (:obj:`int`): number of occurence to partition on

    Returns:
        :obj:`tuple`:

            * :obj:`str`: substring before the nth separator
            * :obj:`str`: separator
            * :obj:`str`: substring after the nth separator

    Raises:
        :obj:`ValueError`: if `sep` is empty or `n` is less than 1
    """
    if not sep:
        raise ValueError('sep cannot be empty')
    if n < 1:
        raise ValueError('n must be at least 1')

    i = find_nth(s, sep, n)
    if i == -1:
        return (s, '', '')
    else:
        if i == 0:
            before = ''
        else:
            before = s[0:i]

        if i == len(s) - len(sep):
            after = ''
        else:
            after = s[i+len(sep):]

        return (before, sep, after)


def rpartition_nth(s, sep, n):
    """ Partition a string on the nth-last occurrence of a substring

    Args:
        s (:obj:`str`): string to partition
        sep (:obj:`str`): separator to partition on
        n (:obj:`int`): number of occurence to partition on

    Returns:
        :obj:`tuple`:

            * :obj:`str`: substring before the nth-last separator
            * :obj:`str`: separator
            * :obj:`str`: substring after the nth-last separator

    Raises:
        :obj:`ValueError`: if `sep` is empty or `n` is less than 1
    """
    if not sep:
        raise ValueError('sep cannot be empty')
    if n < 1:
        raise ValueError('n must be at least 1')

    i = rfind_nth(s, sep, n)
    if i == -1:
        return ('', '', s)
    else:
        if i == 0:
            before = ''
        else:
            before = s[0:i]

        if i == len(s) - len(sep):
            after = ''
        else:
            after = s[i+len(sep):]

        return (before, sep, after)


def camel_case_to_snake_case(camel_case):
    """ Convert string from camel (e.g. SnakeCase) to snake case (e.g. snake_case)

    Args:
        camel_case (:obj:`str`): string in camel case

    Returns:
        :obj:`str`: string in snake case
    """
    _underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
    _underscorer2 = re.compile('([a-z0-9])([A-Z])')

    subbed = _underscorer1.sub(r'\1_\2', camel_case)
    return _underscorer2.sub(r'\1_\2', subbed).lower()
