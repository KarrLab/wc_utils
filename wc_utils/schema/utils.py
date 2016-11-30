""" Utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

# todo: add method to compare (difference) models
from wc_utils.schema.core import Model, Attribute, RelatedAttribute, InvalidObjectSet, InvalidObject, clean_and_validate_objects


def get_attribute_by_verbose_name(cls, verbose_name):
    """ Return the attribute of `Model` class `cls` with verbose name `verbose_name`

    Args:
        cls (:obj:`class`): Model class
        verbose_name (:obj:`str`): verbose attribute name

    Returns:
        :obj:`Attribute`: attribute with verbose name equal to the value of `verbose_name` or `None` if there is no
            matching attribute
    """

    for attr_name, attr in cls.Meta.attributes.items():
        if attr.verbose_name == verbose_name:
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
    return clean_and_validate_objects(objects)


def group_object_set_errors_by_model(errors):
    """ Get object errors grouped by models

    Args:
        errors (:obj:`InvalidObjectSet`): set of object errors

    Returns:
        :obj:`dict`: of errors, with keys equal to instances of `Model` and values lists of `InvalidObject`
    """
    if not errors:
        return None

    errors_by_model = {}
    for obj_err in errors.objects:
        if obj_err.object.__class__ not in errors_by_model:
            errors_by_model[obj_err.object.__class__] = []
        errors_by_model[obj_err.object.__class__].append(obj_err)

    return errors_by_model


def get_object_set_error_string(errors):
    """ Get string representation of object errors, grouped by models and listed by primary key(s)

    Args:
        errors (:obj:`InvalidObjectSet`): set of object errors

    Returns:
        :obj:`str`: string representation of object errors
    """
    if not errors:
        return ''

    str = ''
    for model, object_errs in group_object_set_errors_by_model(errors).items():
        str += '{}:\n'.format(model.Meta.verbose_name_plural)
        for obj_err in object_errs:
            obj = obj_err.object
            str += '  {}:\n'.format(obj.get_primary_attribute())
            for attr_err in obj_err.attributes:
                str += '    {}:\n'.format(attr_err.attribute.name)
                for msg in attr_err.messages:
                    str += '      {}:\n'.format(msg)
    return str
