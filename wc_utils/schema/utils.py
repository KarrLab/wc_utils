""" Utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from __future__ import unicode_literals
from wc_utils.schema.core import Model, Attribute, RelatedAttribute, InvalidObjectSet, InvalidObject, Validator


def get_attribute_by_verbose_name(cls, verbose_name):
    """ Return the attribute of `Model` class `cls` with verbose name `verbose_name`

    Args:
        cls (:obj:`class`): Model class
        verbose_name (:obj:`str`): verbose attribute name

    Returns:
        :obj:`Attribute`: attribute with verbose name equal to the value of `verbose_name` or `None` if there is no
            matching attribute
    """

    if verbose_name is None:
        return None
    for attr_name, attr in cls.Meta.attributes.items():
        if attr.verbose_name.lower() == verbose_name.lower():
            return attr

    return None


def group_objects_by_model(objects):
    """ Group objects by their models

    Args:
        objects (:obj:`list` of `Model`): list of model objects

    Returns:
        :obj:`dict`: dictionary with object grouped by their class
    """
    grouped_objects = {}
    for obj in objects:
        if not obj.__class__ in grouped_objects:
            grouped_objects[obj.__class__] = set()
        grouped_objects[obj.__class__].add(obj)
    return grouped_objects


def get_related_errors(object):
    """ Get all errors associated with an object and its related objects

    Args:
        object (:obj:`Model`): object

    Returns:
        :obj:`InvalidObjectSet`: set of errors
    """
    objects = set((object,)) | object.get_related()
    return Validator().run(objects)
