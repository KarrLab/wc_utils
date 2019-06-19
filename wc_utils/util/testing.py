""" Assertions for testing

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2019-06-18
:Copyright: 2019, Karr Lab
:License: MIT
"""

import humanfriendly
import objsize


def assert_memory_less(obj, size, exclusive=False):
    """ Assert that the memory occupied by an object is less than a
    size

    Args:
        obj (:obj:`object`): object
        size (:obj:`int`): size in bytes
        exclusive (:obj:`bool`, optional): if :obj:`True`, check the exclusive
            memory of the object

    Raises:
        :obj:`ValueError`: if the memory occupied by the object is greater than
            or equal to :obj:`size`
    """
    if exclusive:
        obj_size = objsize.get_exclusive_deep_size(obj)
    else:
        obj_size = objsize.get_deep_size(obj)

    if obj_size >= size:
        raise ValueError("{} memory is greater than or equal to {}".format(
            humanfriendly.format_size(obj_size),
            humanfriendly.format_size(size)))


def assert_memory_less_equal(obj, size, exclusive=False):
    """ Assert that the memory occupied by an object is less than or equal to a
    size

    Args:
        obj (:obj:`object`): object
        size (:obj:`int`): size in bytes
        exclusive (:obj:`bool`, optional): if :obj:`True`, check the exclusive
            memory of the object

    Raises:
        :obj:`ValueError`: if the memory occupied by the object is greater than
            :obj:`size`
    """
    if exclusive:
        obj_size = objsize.get_exclusive_deep_size(obj)
    else:
        obj_size = objsize.get_deep_size(obj)

    if obj_size > size:
        raise ValueError("{} memory is greater than {}".format(
            humanfriendly.format_size(obj_size),
            humanfriendly.format_size(size)))
