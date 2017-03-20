""" String utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-20
:Copyright: 2017, Karr Lab
:License: MIT
"""

from collections import Iterable
from six import string_types


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
        forest (:obj:`list` of `list`): a forest as an iterator of nested iterators
        indentation (:obj:`int`): number of spaces to indent at each level
        depth (:obj:`int`): recursion depth, used by recursion
        keep_trailing_blank_lines (:obj:`Boolean`): if set, keep trailing blank lines in strings in
            `forest`

    Returns:
        :obj:`list` of `str`: list of strings, appropriately indented
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
    return isinstance(o, Iterable) and not isinstance(o, string_types)


def delete_trailing_blanks(l_of_strings):
    """ Remove all blank lines from the end of a list of strings

    A line is blank if it is empty after applying `String.rstrip()`.

    Args:
        l_of_strings (:obj:`list` of `str`): a list of strings
    """
    last = None
    for i, e in reversed(list(enumerate(l_of_strings))):
        e = e.rstrip()
        if e:
            break
        last = i
    if last is not None:
        del l_of_strings[last:]
