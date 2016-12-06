""" Schema

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from collections import OrderedDict
from copy import copy as make_copy, deepcopy as make_deepcopy
from datetime import date, time, datetime
from enum import Enum
from itertools import chain
from math import floor, isnan
from natsort import natsorted, ns
from operator import attrgetter
from six import integer_types, string_types, with_metaclass
from stringcase import sentencecase
from wc_utils.util.types import get_subclasses, get_superclasses
import dateutil.parser
import inflect
import re
import warnings


class ModelMeta(type):

    def __new__(metacls, name, bases, namespace):
        """
        Args:
            name (:obj:`str`): `Model` class name
            bases (:obj: `tuple`): tuple of superclasses
            namespace (:obj:`dict`): namespace of `Model` class definition
        """

        # terminate early so this method is on run on the subclasses of `Model`
        if name == 'Model' and len(bases) == 1 and bases[0] is object:
            return super(ModelMeta, metacls).__new__(metacls, name, bases, namespace)

        # Create new Meta internal class if not provided in class definition so
        # that each model has separate internal Meta classes
        if 'Meta' not in namespace:
            Meta = namespace['Meta'] = type('Meta', (Model.Meta,), {})

            Meta.attribute_order = []
            for base in bases:
                if issubclass(base, Model):
                    for attr_name in base.Meta.attribute_order:
                        if attr_name not in Meta.attribute_order:
                            Meta.attribute_order.append(attr_name)
            Meta.attribute_order = tuple(Meta.attribute_order)

            Meta.unique_together = make_deepcopy(bases[0].Meta.unique_together)
            Meta.tabular_orientation = bases[0].Meta.tabular_orientation
            Meta.frozen_columns = bases[0].Meta.frozen_columns

        # call super class method
        cls = super(ModelMeta, metacls).__new__(metacls, name, bases, namespace)

        # Initialize meta data
        metacls.init_inheritance(cls)

        metacls.init_attributes(cls)

        metacls.init_primary_attribute(cls)

        cls.Meta.related_attributes = {}
        for model in get_subclasses(Model):
            metacls.init_related_attributes(model)

        metacls.init_attribute_order(cls)

        metacls.init_verbose_names(cls)

        metacls.validate_attributes(cls)

        # Return new class
        return cls

    def init_inheritance(cls):
        """ Get tuple of this model and superclasses which are subclasses of `Model` """
        cls.Meta.inheritance = tuple([cls] + [supercls for supercls in get_superclasses(cls)
                                              if issubclass(supercls, Model) and supercls is not Model])

    def init_attributes(cls):
        """ Initialize attributes """
        cls.Meta.attributes = dict()
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Attribute):
                attr.name = attr_name
                if not attr.verbose_name:
                    attr.verbose_name = sentencecase(attr_name)
                cls.Meta.attributes[attr_name] = attr

            if isinstance(attr, RelatedAttribute):
                if attr.name in cls.__dict__:
                    attr.primary_class = cls

    def init_related_attributes(cls):
        """ Initialize related attributes """
        for attr in cls.Meta.attributes.values():
            if isinstance(attr, RelatedAttribute):

                # deserialize related class references by class name
                if isinstance(attr.related_class, string_types):
                    related_class_name = attr.related_class
                    if '.' not in related_class_name:
                        related_class_name = cls.__module__ + '.' + related_class_name

                    related_class = get_model(related_class_name)
                    if related_class:
                        attr.related_class = related_class

                # setup related attributes on related classes
                if attr.name in cls.__dict__ and attr.related_name and isinstance(attr.related_class, type) and issubclass(attr.related_class, Model):
                    related_classes = chain([attr.related_class], get_subclasses(attr.related_class))
                    for related_class in related_classes:
                        # check that related class has primary attributes

                        if isinstance(attr, (OneToManyAttribute, ManyToManyAttribute)) and \
                                attr.__class__ is not OneToManyAttribute and attr.__class__ is not ManyToManyAttribute and \
                                'serialize' in attr.__class__.__dict__ and 'deserialize' in attr.__class__.__dict__:
                            pass
                        elif not related_class.Meta.primary_attribute:
                            if related_class.Meta.tabular_orientation == TabularOrientation['inline']:
                                warnings.warn('Related class {} must have a primary attribute'.format(
                                    related_class.__name__))
                            else:
                                raise ValueError('Related class {} must have a primary attribute'.format(
                                    related_class.__name__))
                        elif not related_class.Meta.primary_attribute.unique:
                            if related_class.Meta.tabular_orientation == TabularOrientation['inline']:
                                warnings.warn('Primary attribute {} of related class {} must be unique'.format(
                                    related_class.Meta.primary_attribute.name, related_class.__name__))
                            else:
                                raise ValueError('Primary attribute {} of related class {} must be unique'.format(
                                    related_class.Meta.primary_attribute.name, related_class.__name__))

                        # check that name doesn't conflict with another attribute
                        if attr.related_name in related_class.Meta.attributes:
                            other_attr = related_class.Meta.attributes[attr.related_name]
                            raise ValueError('Related attribute {}.{} cannot use the same related name as {}.{}'.format(
                                cls.__name__, attr_name,
                                related_class.__name__, attr.related_name,
                            ))

                        # check that name doesn't clash with another related attribute from a different model
                        if attr.related_name in related_class.Meta.related_attributes and related_class.Meta.related_attributes[attr.related_name] is not attr:
                            other_attr = related_class.Meta.related_attributes[attr.related_name]
                            raise ValueError('Attributes {}.{} and {}.{} cannot use the same related attribute name {}.{}'.format(
                                cls.__name__, attr_name,
                                other_attr.primary_model.__name__, other_attr.name,
                                related_class.__name__, attr.related_name,
                            ))

                        # add attribute to dictionary of related attributes
                        related_class.Meta.related_attributes[attr.related_name] = attr

    def init_primary_attribute(cls):
        """ Initialize the primary attribute of a model """
        primary_attributes = [attr for attr in cls.Meta.attributes.values() if attr.primary]

        if len(primary_attributes) == 0:
            cls.Meta.primary_attribute = None

        elif len(primary_attributes) == 1:
            cls.Meta.primary_attribute = primary_attributes[0]

        else:
            raise ValueError('Model {} cannot have more than one primary attribute'.format(cls.__name__))

    def init_attribute_order(cls):
        """ Initialize the order in which the attributes should be printed across Excel columns """
        ordered_attributes = list(cls.Meta.attribute_order or ())

        unordered_attributes = set()
        for base in cls.Meta.inheritance:
            for attr_name in base.__dict__.keys():
                if isinstance(getattr(base, attr_name), Attribute) and attr_name not in ordered_attributes:
                    unordered_attributes.add(attr_name)

        unordered_attributes = natsorted(unordered_attributes, alg=ns.IGNORECASE)

        cls.Meta.attribute_order = tuple(ordered_attributes + unordered_attributes)

    def init_verbose_names(cls):
        """ Initialize the singular and plural verbose names of a model """
        if not cls.Meta.verbose_name:
            cls.Meta.verbose_name = sentencecase(cls.__name__)

        if not cls.Meta.verbose_name_plural:
            inflect_engine = inflect.engine()
            cls.Meta.verbose_name_plural = inflect_engine.plural(cls.Meta.verbose_name)

    def validate_attributes(cls):
        """ Validate attribute values """

        # `attribute_order` is a tuple of attribute names
        if not isinstance(cls.Meta.attribute_order, tuple):
            raise ValueError('{}.attribute_order must be a tuple of attribute names'.format(cls.__name__))

        for attr_name in cls.Meta.attribute_order:
            if not isinstance(attr_name, str):
                raise ValueError('{}.attribute_order must be a tuple of attribute names'.format(cls.__name__))

            if attr_name not in cls.Meta.attributes:
                raise ValueError('{}.attribute_order must be a tuple of attribute names'.format(cls.__name__))

        # `unique_together` is a tuple of tuple of attribute names
        if not isinstance(cls.Meta.unique_together, tuple):
            raise ValueError('`unique_together` must be a tuple of tuple of attribute names')

        for unique_together in cls.Meta.unique_together:
            if not isinstance(unique_together, tuple):
                raise ValueError('`unique_together` must be a tuple of tuple of attribute names')

            for attr_name in unique_together:
                if not isinstance(attr_name, str):
                    raise ValueError('`unique_together` must be a tuple of tuple of attribute names')

                if attr_name not in cls.Meta.attributes:
                    raise ValueError('`unique_together` must be a tuple of tuple of attribute names')

            if len(set(unique_together)) < len(unique_together):
                raise ValueError('`unique_together` cannot contain repeated attribute names with each tuple')

        if len(set(cls.Meta.unique_together)) < len(cls.Meta.unique_together):
            raise ValueError('`unique_together` cannot contain repeated tuples')

    @staticmethod
    def validate_related_attributes(cls):
        """ Validate attribute values """

        for attr_name, attr in cls.Meta.attributes.items():
            if isinstance(attr, RelatedAttribute) and not (isinstance(attr.related_class, type) and issubclass(attr.related_class, Model)):
                raise ValueError('Related class {} of {}.{} must be defined'.format(
                    attr.related_class, attr.primary_class.__name__, attr_name))

        # tabular orientation
        if cls.Meta.tabular_orientation == TabularOrientation['inline']:
            for attr in cls.Meta.related_attributes.values():
                if attr in [OneToManyAttribute, OneToManyAttribute, ManyToOneAttribute, ManyToManyAttribute]:
                    raise ValueError(
                        'Inline model "{}" must define their own serialization/deserialization methods'.format(cls.__name__))

                if 'deserialize' not in attr.__class__.__dict__:
                    raise ValueError(
                        'Inline model "{}" must define their own serialization/deserialization methods'.format(cls.__name__))

            if len(cls.Meta.related_attributes) == 0:
                raise ValueError(
                    'Inline model "{}" should have a single required related one-to-one or one-to-many attribute'.format(cls.__name__))
            elif len(cls.Meta.related_attributes) == 1:
                attr = list(cls.Meta.related_attributes.values())[0]

                if not isinstance(attr, (OneToOneAttribute, OneToManyAttribute)):
                    warnings.warn(
                        'Inline model "{}" should have a single required related one-to-one or one-to-many attribute'.format(cls.__name__))

                elif attr.related_none:
                    warnings.warn(
                        'Inline model "{}" should have a single required related one-to-one or one-to-many attribute'.format(cls.__name__))
            else:
                warnings.warn(
                    'Inline model "{}" should have a single required related one-to-one or one-to-many attribute'.format(cls.__name__))


class TabularOrientation(Enum):
    row = 1
    column = 2
    inline = 3


class Model(with_metaclass(ModelMeta, object)):
    """ Base object model """

    class Meta(object):
        """ Meta data for :class:`Model`

        Attributes:
            attributes (:obj:`set` of `Attribute`): attributes
            related_attributes(:obj:`set` of `Attribute`): attributes declared in related objects
            primary_attribute (:obj:`Attribute`): attributes with `primary`=True
            attribute_order (:obj:`tuple` of `str`): tuple of attribute names, in the order in which they should be displayed
            verbose_name (:obj:`str`): verbose name to refer to a instance of the model
            verbose_name_plural (:obj:`str`): plural verbose name to refer to instances of the model
            tabular_orientation (:obj:`TabularOrientation`): orientation of model objects in table (e.g. Excel)
            frozen_columns (:obj:`int`): number of Excel columns to freeze
            inheritance (:obj:`tuple` of `class`): tuple of all superclasses
        """
        attributes = None
        related_attributes = None
        primary_attribute = None
        unique_together = ()
        attribute_order = ()
        verbose_name = ''
        verbose_name_plural = ''
        tabular_orientation = TabularOrientation['row']
        frozen_columns = 1
        inheritance = None

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs (:obj:`dict`, optional): dictionary of keyword arguments with keys equal to the names of the model attributes
        """

        """ check that related classes of attributes are defined """
        self.__class__.validate_related_attributes(self.__class__)

        """ initialize attributes """
        # attributes
        for attr in self.Meta.attributes.values():
            super(Model, self).__setattr__(attr.name, attr.get_init_value(self))

        # related attributes
        for attr in self.Meta.related_attributes.values():
            super(Model, self).__setattr__(attr.related_name, attr.get_init_related_value(self))

        """ process arguments """
        for attr_name, val in kwargs.items():
            if attr_name not in self.Meta.attributes and attr_name not in self.Meta.related_attributes:
                raise TypeError("'{:s}' is an invalid keyword argument for {}.__init__".format(
                    attr_name, self.__class__.__name__))
            setattr(self, attr_name, val)

    def __setattr__(self, attr_name, value, propagate=True):
        """ Set attribute

        Args:
            attr_name (:obj:`str`): attribute name
            value (:obj:`object`): value
            propagate (:obj:`bool`, optional): propagate change through attribute `set_value` and `set_related_value`
        """
        if propagate:
            if attr_name in self.__class__.Meta.attributes:
                attr = self.__class__.Meta.attributes[attr_name]
                value = attr.set_value(self, value)

            elif attr_name in self.__class__.Meta.related_attributes:
                attr = self.__class__.Meta.related_attributes[attr_name]
                value = attr.set_related_value(self, value)

        super(Model, self).__setattr__(attr_name, value)

    def __eq__(self, other, _seen=None):
        """ Determine if two objects are semantically equal

        Args:
            other (:obj:`Model`): object to compare
            _seen (:obj:`set`, optional): pairs of objects that have already been compared

        Returns:
            :obj:`bool`: `True` if objects are semantically equal, else `False`
        """
        if _seen is None:
            _seen = set()
        if (self, other) in _seen:
            return True
        _seen.add((self, other))

        if self is other:
            return True

        if not self.__class__ is other.__class__:
            return False

        for attr_name in chain(self.Meta.attributes.keys(), self.Meta.related_attributes.keys()):
            val = getattr(self, attr_name)
            other_val = getattr(other, attr_name)

            if isinstance(val, Model):
                if not val.__eq__(other_val, _seen):
                    return False

            elif isinstance(val, (set, list)):
                if not isinstance(other_val, (set, list)):
                    return False

                if len(val) != len(other_val):
                    return False

                for v in val:
                    match = False
                    for ov in other_val:
                        if v.__eq__(ov, _seen):
                            match = True
                            break
                    if not match:
                        return False

            elif val != other_val:
                return False

        return True

    def __ne__(self, other):
        """ Determine if two objects are semantically unequal

        Args:
            other (:obj:`object`): object to compare

        Returns:
            :obj:`bool`: `False` if objects are semantically equal, else `True`
        """
        return not self.__eq__(other)

    def __hash__(self):
        """ Returns a hash for a object

        Returns:
            :obj:`int`: hash code
        """
        return id(self)

    def __str__(self):
        """ Get the string representation of an object

        Returns:
            :obj:`str`: string representation of object
        """

        if self.__class__.Meta.primary_attribute:
            return '<{}.{}: {}>'.format(self.__class__.__module__, self.__class__.__name__, getattr(self, self.__class__.Meta.primary_attribute.name))

        return super(Model, self).__str__()

    def diff(self, other, _seen=None):
        """ Get difference between two model objects

        Args:
            other (:obj:`Model`): other model object
            _seen (:obj:`set`, optional): pairs of objects that have already been compared

        Returns:
            :obj:`str`: difference message
        """
        othr = other

        if _seen is None:
            _seen = set()

        if (self, othr) in _seen:
            return ''
        _seen.add((self, othr))

        cls_self = self.__class__
        cls_othr = othr.__class__
        if cls_self is not cls_othr:
            return 'Objects have different types "{}" and "{}"'.format(cls_self, cls_othr)

        cls = cls_othr
        msgs = []

        attr_names = natsorted(chain(cls.Meta.attributes.keys(), cls.Meta.related_attributes.keys()), alg=ns.IGNORECASE)
        for attr_name in attr_names:
            val_self = getattr(self, attr_name)
            val_othr = getattr(othr, attr_name)

            if isinstance(val_self, Model):
                msg = val_self.diff(val_othr, _seen)

            elif isinstance(val_self, (set, list)):
                if not isinstance(val_othr, (set, list)):
                    msg = 'Class: {} != Class: {}'.format(val_self, val_othr)

                elif len(val_self) != len(val_othr):
                    msg = 'Length: {} != Length: {}'.format(len(val_self), len(val_othr))

                else:
                    attr_msgs = []
                    for v_self in val_self:
                        serial_self = v_self.serialize()

                        match = None
                        for v_othr in val_othr:
                            serial_othr = v_othr.serialize()

                            if serial_self == serial_othr:
                                attr_msg = v_self.diff(v_othr, _seen)
                                if serial_self or not attr_msg:
                                    match = serial_othr
                                    break

                        if match:
                            if attr_msg:
                                attr_msgs.append('element: "{}" != element: "{}"\n  {}'.format(
                                    serial_self, serial_othr, attr_msg.replace('\n', '\n  ')))
                        else:
                            attr_msgs.append('No matching element {}'.format(serial_self))

                    msg = '\n'.join(attr_msgs)

            elif val_self != val_othr:
                msg = '{} != {}'.format(val_self, val_othr)

            else:
                msg = ''

            if msg:
                msgs.append('`{}` are not equal:\n  {}'.format(attr_name, msg.replace('\n', '\n  ')))

        if msgs:
            id_self = self.serialize() or 'instance: '
            id_othr = othr.serialize()

            if id_self:
                id_self = '"' + id_self + '"'
            else:
                id_self = 'instance: ' + cls.__name__

            if id_othr:
                id_othr = '"' + id_othr + '"'
            else:
                id_othr = 'instance: ' + cls.__name__

            return 'Objects ({}, {}) have different attribute values:\n  {}'.format(id_self, id_othr, '\n'.join(msgs).replace('\n', '\n  '))

        return ''

    def get_primary_attribute(self):
        """ Get values of primary attribute

        Returns:
            :obj:`object`: values of primary attribute
        """
        if self.__class__.Meta.primary_attribute:
            return getattr(self, self.__class__.Meta.primary_attribute.name)

        return None

    def serialize(self):
        """ Get value of primary attribute

        Returns:
            :obj:`str`: value of primary attribute
        """
        return self.get_primary_attribute()

    @classmethod
    def deserialize(cls, value, objects):
        """ Deserialize value

        Args:
            value (:obj:`str`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if value in objects[cls]:
            return (objects[cls][value], None)

        attr = cls.Meta.primary_attribute
        return (None, InvalidAttribute(attr, ['No object with primary attribute value "{}"'.format(value)]))

    def get_related(self, _related_objects=None):
        """ Get all related objects

        Args:
            _related_objects (:obj:`set` of `Model`): preliminary set of related objects

        Returns:
            :obj:`set` of `Model`: related objects
        """
        if _related_objects is None:
            _related_objects = set()

        cls = self.__class__

        for attr in cls.Meta.attributes.values():
            if isinstance(attr, RelatedAttribute):
                value = getattr(self, attr.name)

                if isinstance(value, set):
                    for v in value:
                        if v not in _related_objects:
                            _related_objects.add(v)
                            v.get_related(_related_objects)
                elif value is not None and value not in _related_objects:
                    _related_objects.add(value)
                    value.get_related(_related_objects)

        for attr in cls.Meta.related_attributes.values():
            value = getattr(self, attr.related_name)

            if isinstance(value, set):
                for v in value:
                    if v not in _related_objects:
                        _related_objects.add(v)
                        v.get_related(_related_objects)
            elif value is not None and value not in _related_objects:
                _related_objects.add(value)
                value.get_related(_related_objects)

        return _related_objects

    def clean(self):
        """ Clean all of the object's attributes

        Returns:
            :obj:`InvalidObject` or None: `None` if the object is valid,
                otherwise return a list of errors as an instance of `InvalidObject`
        """
        errors = []

        for attr_name, attr in self.Meta.attributes.items():
            value = getattr(self, attr_name)
            clean_value, error = attr.clean(value)

            if error:
                errors.append(error)
            else:
                self.__setattr__(attr_name, clean_value)

        if errors:
            return InvalidObject(self, errors)
        return None

    def validate(self):
        """ Determine if the object is valid

        Returns:
            :obj:`InvalidObject` or None: `None` if the object is valid,
                otherwise return a list of errors as an instance of `InvalidObject`
        """
        errors = []

        # attributes
        for attr_name, attr in self.Meta.attributes.items():
            error = attr.validate(self, getattr(self, attr_name))
            if error:
                errors.append(error)

        # related attributes
        for attr_name, attr in self.Meta.related_attributes.items():
            if attr.related_name:
                error = attr.related_validate(self, getattr(self, attr.related_name))
                if error:
                    errors.append(error)

        if errors:
            return InvalidObject(self, errors)
        return None

    @classmethod
    def validate_unique(cls, objects):
        """ Validate attribute uniqueness

        Args:
            objects (:obj:`set` of `Model`): set of objects

        Returns:
            :obj:`InvalidModel` or `None`: list of invalid attributes and their errors
        """
        errors = []

        # validate uniqueness of individual attributes
        for attr_name, attr in cls.Meta.attributes.items():
            if attr.unique:
                vals = []
                for obj in objects:
                    vals.append(getattr(obj, attr_name))

                error = attr.validate_unique(objects, vals)
                if error:
                    errors.append(error)

        # validate uniqueness of combinations of attributes
        for unique_together in cls.Meta.unique_together:
            vals = set()
            rep_vals = set()
            for obj in objects:
                val = tuple([getattr(obj, attr_name) for attr_name in unique_together])
                if val in vals:
                    rep_vals.add(val)
                else:
                    vals.add(val)

            if rep_vals:
                msg = 'Combinations of ({}) must be unique. The following combinations are repeated:'.format(
                    ', '.join(unique_together))
                for rep_val in rep_vals:
                    msg += '\n- {}'.format(', '.join(rep_val))
                attr = cls.Meta.attributes[list(unique_together)[0]]
                errors.append(InvalidAttribute(attr, [msg]))

        # return
        if errors:
            return InvalidModel(cls, errors)
        return None

    def copy(self):
        """ Create a copy

        Returns:
            :obj:`Model`: model copy
        """

        # initialize copies of objects
        objects_and_copies = {}
        for obj in chain([self], self.get_related()):
            copy = obj.__class__()
            objects_and_copies[obj] = copy

        # copy attribute values
        for obj, copy in objects_and_copies.items():
            obj._copy_attributes(copy, objects_and_copies)

        # return copy
        return objects_and_copies[self]

    def _copy_attributes(self, copy, objects_and_copies):
        """ Copy the attributes from `self` to its new copy, `copy`

        Args:
            copy (:obj:`Model`): object to copy attribute values to
            objects_and_copies (:obj:`dict` of `Model`: `Model`): dictionary of pairs of objects and their new copies
        """
        # get class
        cls = self.__class__

        # copy attributes
        for attr in cls.Meta.attributes.values():
            val = getattr(self, attr.name)

            if isinstance(attr, RelatedAttribute):
                if val is None:
                    copy_val = val
                elif isinstance(val, Model):
                    copy_val = objects_and_copies[val]
                elif isinstance(val, (set, list, tuple)):
                    copy_val = []
                    for v in val:
                        copy_val.append(objects_and_copies[v])
                else:
                    raise ValueError('Invalid related attribute value')
            else:
                if val is None:
                    copy_val = val
                elif isinstance(val, (string_types, bool, integer_types, float, Enum, )):
                    copy_val = make_copy(val)
                else:
                    raise ValueError('Invalid related attribute value')

            setattr(copy, attr.name, copy_val)


class Attribute(object):
    """ Model attribute

    Attributes:
        name (:obj:`str`): name
        default (:obj:`object`): default value
        verbose_name (:obj:`str`): verbose name
        help (:obj:`str`): help string
        primary (:obj:`bool`): indicate if attribute is primary attribute
        unique (:obj:`bool`): indicate if attribute value must be unique
        unique_case_insensitive (:obj:`bool`): if true, conduct case-insensitive test of uniqueness
    """

    def __init__(self, default=None, verbose_name='', help='',
                 primary=False, unique=False, unique_case_insensitive=False):
        """
        Args:
            default (:obj:`object`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
            unique_case_insensitive (:obj:`bool`, optional): if true, conduct case-insensitive test of uniqueness
        """
        self.name = None
        self.default = default
        self.verbose_name = verbose_name
        self.primary = primary
        self.unique = unique
        self.unique_case_insensitive = unique_case_insensitive

    def get_init_value(self, obj):
        """ Get initial value for attribute

        Args:
            obj (:obj:`Model`): object whose attribute is being initialized

        Returns:
            :obj:`object`: initial value
        """
        return make_copy(self.default)

    def set_value(self, obj, new_value):
        """ Set value of attribute of object

        Args:
            obj (:obj:`Model`): object
            new_value (:obj:`object`): new attribute value

        Returns:
            :obj:`object`: attribute value
        """
        return new_value

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        return (value, None)

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, otherwise return a list of errors as an instance of `InvalidAttribute`
        """
        return None

    def validate_unique(self, objects, values):
        """ Determine if the attribute values are unique

        Args:
            objects (:obj:`set` of `Model`): set of `Model` objects
            values (:obj:`list`): list of values

        Returns:
           :obj:`InvalidAttribute` or None: None if values are unique, otherwise return a list of errors as an instance of `InvalidAttribute`
        """
        unq_vals = set()
        rep_vals = set()

        for val in values:
            if self.unique_case_insensitive and isinstance(val, string_types):
                val = val.lower()
            if val in unq_vals:
                rep_vals.add(val)
            else:
                unq_vals.add(val)

        if rep_vals:
            message = 'Values must be unique. The following values are repeated:\n- ' + '\n- '.join(rep_vals)
            return InvalidAttribute(self, [message])

    def serialize(self, value):
        """ Serialize value

        Args:
            value (:obj:`object`): Python representation

        Returns:
            :obj:`bool`, `float`, `str`, or `None`: simple Python representation
        """
        return value

    def deserialize(self, value):
        """ Deserialize value

        Args:
            value (:obj:`object`): semantically equivalent representation

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        return self.clean(value)


class EnumAttribute(Attribute):
    """ Enumeration attribute

    Attributes:
        enum_class (:obj:`type`): subclass of `Enum`
    """

    def __init__(self, enum_class, default=None, verbose_name='', help='',
                 primary=False, unique=False, unique_case_insensitive=False):
        """
        Args:
            enum_class (:obj:`type`): subclass of `Enum`
            default (:obj:`object`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
            unique_case_insensitive (:obj:`bool`, optional): if true, conduct case-insensitive test of uniqueness
        """
        if not issubclass(enum_class, Enum):
            raise ValueError('`enum_class` must be an subclass of `Enum`')
        if default is not None and not isinstance(default, enum_class):
            raise ValueError('Default must be None or an instance of `enum_class`')

        super(EnumAttribute, self).__init__(default=default,
                                            verbose_name=verbose_name, help=help,
                                            primary=primary, unique=unique, unique_case_insensitive=unique_case_insensitive)

        self.enum_class = enum_class

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `Enum`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        error = None

        if isinstance(value, string_types):
            if value in self.enum_class.__members__:
                value = self.enum_class[value]
            else:
                error = 'Value must be convertible to an instance of {}'.format(self.enum_class.__name__)

        elif isinstance(value, (integer_types, float)):
            try:
                value = self.enum_class(value)
            except ValueError:
                error = 'Value must be convertible to an instance of {}'.format(self.enum_class.__name__)

        elif not isinstance(value, self.enum_class):
            error = 'Value must be an instance of `{}`'.format(self.enum_class.__name__)

        if error:
            return (None, InvalidAttribute(self, [error]))
        else:
            return (value, None)

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(EnumAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not isinstance(value, self.enum_class):
            errors.append('Value must be an instance of `{}`'.format(self.enum_class.__name__))

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize enumeration

        Args:
            value (:obj:`Enum`): Python representation

        Returns:
            :obj:`str`: simple Python representation
        """
        return value.name


class BooleanAttribute(Attribute):
    """ Boolean attribute

    Attributes:
        default (:obj:`bool`): default value
    """

    def __init__(self, default=False, verbose_name='', help='Enter a Boolean value'):
        """
        Args:
            default (:obj:`float`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
        """
        if default is not None and not isinstance(default, bool):
            raise ValueError('`default` must be None or an instance of `bool`')

        super(BooleanAttribute, self).__init__(default=default,
                                               verbose_name=verbose_name, help=help,
                                               primary=False, unique=False, unique_case_insensitive=False)

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `bool`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        errors = []
        if isinstance(value, string_types):
            if value == '':
                value = None
            elif value in ['true', 'True', 'TRUE', '1']:
                value = True
            elif value in ['false', 'False', 'FALSE', '0']:
                value = False

        try:
            float_value = float(value)

            if isnan(float_value):
                value = None
            elif float_value == 0.:
                value = False
            elif float_value == 1.:
                value = True
        except ValueError:
            pass

        if (value is None) or isinstance(value, bool):
            return (value, None)
        return (None, InvalidAttribute(attr, ['Value must be a `bool` or `None`']))

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(BooleanAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is not None and not isinstance(value, bool):
            errors.append('Value must be an instance of `bool` or `None`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize value

        Args:
            value (:obj:`bool`): Python representation

        Returns:
            :obj:`bool`: simple Python representation
        """
        return value


class FloatAttribute(Attribute):
    """ Float attribute

    Attributes:
        default (:obj:`float`): default value
        min (:obj:`float`): minimum value
        max (:obj:`float`): maximum value
        nan (:obj:`bool`): if true, allow nan values
    """

    def __init__(self, min=float('nan'), max=float('nan'), nan=True,
                 default=float('nan'), verbose_name='', help='',
                 primary=False, unique=False):
        """
        Args:
            min (:obj:`float`, optional): minimum value
            max (:obj:`float`, optional): maximum value
            nan (:obj:`bool`, optional): if true, allow nan values
            default (:obj:`float`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        min = float(min)
        max = float(max)
        default = float(default)
        if not isnan(min) and not isnan(max) and max < min:
            raise ValueError('max must be at least min')

        super(FloatAttribute, self).__init__(default=default,
                                             verbose_name=verbose_name, help=help,
                                             primary=primary, unique=unique, unique_case_insensitive=False)

        self.min = min
        self.max = max
        self.nan = nan

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `float`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if value is None or (isinstance(value, string_types) and value == ''):
            value = float('nan')

        try:
            value = float(value)
            return (value, None)
        except ValueError:
            return (None, InvalidAttribute(self, 'Value must be a `float`'))

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(FloatAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if isinstance(value, float):
            if not self.nan and isnan(value):
                errors.append('Value cannot be `nan`')

            if (not isnan(self.min)) and (not isnan(value)) and (value < self.min):
                errors.append('Value must be at least {:f}'.format(self.min))

            if (not isnan(self.max)) and (not isnan(value)) and (value > self.max):
                errors.append('Value must be at most {:f}'.format(self.max))
        else:
            errors.append('Value must be an instance of `float`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize float

        Args:
            value (:obj:`float`): Python representation

        Returns:
            :obj:`float`: simple Python representation
        """
        if isnan(value):
            return None
        return value


class IntegerAttribute(Attribute):
    """ Interger attribute

    Attributes:
        default (:obj:`int`): default value
        min (:obj:`int`): minimum value
        max (:obj:`int`): maximum value
    """

    def __init__(self, min=None, max=None, default=None, verbose_name='', help='', primary=False, unique=False):
        """
        Args:
            min (:obj:`int`, optional): minimum value
            max (:obj:`int`, optional): maximum value
            default (:obj:`int`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        if min is not None:
            min = int(min)
        if max is not None:
            max = int(max)
        if default is not None:
            default = int(default)
        if min is not None and max is not None and max < min:
            raise ValueError('max must be at least min')

        super(IntegerAttribute, self).__init__(default=default,
                                               verbose_name=verbose_name, help=help,
                                               primary=primary, unique=unique, unique_case_insensitive=False)

        self.min = min
        self.max = max

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `int`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """

        if value is None or (isinstance(value, string_types) and value == ''):
            return (value, None, )

        try:
            if float(value) == int(float(value)):
                return (int(float(value)), None, )
        except ValueError:
            pass
        return (None, InvalidAttribute(self, ['Value must be an integer']), )

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(IntegerAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if isinstance(value, integer_types):
            if self.min is not None:
                if value is None:
                    errors.append('Value cannot be None')
                elif value < self.min:
                    errors.append('Value must be at least {:d}'.format(self.min))

            if self.max is not None:
                if value is None:
                    errors.append('Value cannot be None')
                elif value > self.max:
                    errors.append('Value must be at most {:d}'.format(self.max))
        elif value is not None:
            errors.append('Value must be an instance of `int` or `None`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize interger

        Args:
            value (:obj:`int`): Python representation

        Returns:
            :obj:`float`: simple Python representation
        """
        if value is None:
            return None
        return float(value)


class PositiveIntegerAttribute(IntegerAttribute):
    """ Positive interger attribute """

    def __init__(self, max=None, default=None, verbose_name='', help='', primary=False, unique=False):
        """
        Args:
            min (:obj:`int`, optional): minimum value
            max (:obj:`int`, optional): maximum value
            default (:obj:`int`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        super(PositiveIntegerAttribute, self).__init__(min=None, max=max, default=default,
                                                       verbose_name=verbose_name, help=help,
                                                       primary=primary, unique=unique)

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """

        error = super(PositiveIntegerAttribute, self).validate(obj, value)
        if error:
            errors = error.messages
        else:
            errors = []

        if (value is not None) and (float(value) <= 0):
            errors.append('Value must be positive')

        if errors:
            return InvalidAttribute(self, errors)
        return None


class StringAttribute(Attribute):
    """ String attribute

    Attributes:
        default (:obj:`str`, optional): default value
        min_length (:obj:`int`): minimum length
        max_length (:obj:`int`): maximum length
    """

    def __init__(self, min_length=0, max_length=255, default='', verbose_name='', help='',
                 primary=False, unique=False, unique_case_insensitive=False):
        """
        Args:
            min_length (:obj:`int`, optional): minimum length
            max_length (:obj:`int`, optional): maximum length
            default (:obj:`str`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
            unique_case_insensitive (:obj:`bool`, optional): if true, conduct case-insensitive test of uniqueness
        """

        if not isinstance(min_length, integer_types) or min_length < 0:
            raise ValueError('min_length must be a non-negative integer')
        if (max_length is not None) and (not isinstance(max_length, integer_types) or max_length < 0):
            raise ValueError('max_length must be None or a non-negative integer')
        if not isinstance(default, string_types):
            raise ValueError('Default must be a string')

        super(StringAttribute, self).__init__(default=default,
                                              verbose_name=verbose_name, help=help,
                                              primary=primary, unique=unique, unique_case_insensitive=unique_case_insensitive)

        self.min_length = min_length
        self.max_length = max_length

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `str`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if value is None:
            value = ''
        elif not isinstance(value, string_types):
            value = str(value)
        return (value, None)

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(StringAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not isinstance(value, string_types):
            errors.append('Value must be an instance of `str`')
        else:
            if self.min_length and len(value) < self.min_length:
                errors.append('Value must be at least {:d} characters'.format(self.min_length))

            if self.max_length and len(value) > self.max_length:
                errors.append('Value must be less than {:d} characters'.format(self.max_length))

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize string

        Args:
            value (:obj:`str`): Python representation

        Returns:
            :obj:`str`: simple Python representation
        """
        return value


class LongStringAttribute(StringAttribute):
    """ Long string attribute """

    def __init__(self, min_length=0, max_length=2**32 - 1, default='', verbose_name='', help='',
                 primary=False, unique=False, unique_case_insensitive=False):
        """
        Args:
            min_length (:obj:`int`, optional): minimum length
            max_length (:obj:`int`, optional): maximum length
            default (:obj:`str`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
            unique_case_insensitive (:obj:`bool`, optional): if true, conduct case-insensitive test of uniqueness
        """

        super(LongStringAttribute, self).__init__(min_length=min_length, max_length=max_length, default=default,
                                                  verbose_name=verbose_name, help=help,
                                                  primary=primary, unique=unique, unique_case_insensitive=unique_case_insensitive)


class RegexAttribute(StringAttribute):
    """ Regular expression attribute

    Attributes:
        pattern (:obj:`str`): regular expression pattern
        flags (:obj:`int`): regular expression flags
    """

    def __init__(self, pattern, flags=None, min_length=0, max_length=None, default='', verbose_name='', help='',
                 primary=False, unique=False):
        """
        Args:
            pattern (:obj:`str`): regular expression pattern
            flags (:obj:`int`, optional): regular expression flags
            min_length (:obj:`int`, optional): minimum length
            max_length (:obj:`int`, optional): maximum length
            default (:obj:`str`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """

        if flags is not None:
            unique_case_insensitive = bin(flags)[-2] == '1'
        else:
            unique_case_insensitive = False

        super(RegexAttribute, self).__init__(min_length=min_length, max_length=max_length,
                                             default=default, verbose_name=verbose_name, help=help,
                                             primary=primary, unique=unique, unique_case_insensitive=unique_case_insensitive)
        self.pattern = pattern
        self.flags = flags

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`object`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(RegexAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not re.match(self.pattern, value, flags=self.flags):
            errors.append('Value "{}" does not match pattern: {}'.format(value, self.pattern))

        if errors:
            return InvalidAttribute(self, errors)
        return None


class SlugAttribute(RegexAttribute):
    """ Slug attribute to be used for string IDs """

    def __init__(self, verbose_name='', help=None, primary=True, unique=True):
        """
        Args:
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
        """
        if help is None:
            help = 'Enter a unique string identifier that (1) starts with a letter, (2) is composed of letters, numbers and underscopes, and (3) is less than 64 characters long'

        super(SlugAttribute, self).__init__(pattern=r'^[a-z_][a-z0-9_]*$', flags=re.I,
                                            min_length=1, max_length=63,
                                            default='', verbose_name=verbose_name, help=help,
                                            primary=primary, unique=unique)


class UrlAttribute(RegexAttribute):
    """ URL attribute to be used for URLs """

    def __init__(self, verbose_name='URL', help='Enter a valid URL', primary=False, unique=False):
        """
        Args:
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        super(UrlAttribute, self).__init__(pattern=r'^(?:http|ftp)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$',
                                           flags=re.I,
                                           min_length=1, max_length=2**16 - 1,
                                           default='', verbose_name=verbose_name, help=help,
                                           primary=primary, unique=unique)


class DateAttribute(Attribute):
    """ Date attribute

    Attributes:
        none (:obj:`bool`): if true, the attribute is invalid if its value is None
        default (:obj:`date`): default date
    """

    def __init__(self, none=True, default=None, verbose_name='', help='', primary=False, unique=False):
        """
        Args:
            none (:obj:`bool`, optional): if true, the attribute is invalid if its value is None
            default (:obj:`date`, optional): default date
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        super(DateAttribute, self).__init__(default=default,
                                            verbose_name=verbose_name, help=help,
                                            primary=primary, unique=unique)
        self.none = none

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `date`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if value is None:
            return (value, None)

        if isinstance(value, date):
            return (value, None)

        if isinstance(value, datetime):
            if value.hour == 0 and value.minute == 0 and value.second == 0 and value.microsecond == 0:
                return (value.date(), None)
            else:
                return (None, InvalidAttribute(self, ['Time must be 0:0:0.0']))

        if isinstance(value, string_types):
            try:
                datetime_value = dateutil.parser.parse(value)
                if datetime_value.hour == 0 and datetime_value.minute == 0 and datetime_value.second == 0 and datetime_value.microsecond == 0:
                    return (datetime_value.date(), None)
                else:
                    return (None, InvalidAttribute(self, ['Time must be 0:0:0.0']))
            except ValueError:
                return (None, InvalidAttribute(self, ['String must be a valid date']))

        try:
            float_value = float(value)
            int_value = int(float_value)
            if float_value == int_value:
                return (date.fromordinal(int_value + date(1900, 1, 1).toordinal() - 1), None)
        except ValueError:
            pass

        return (None, 'Value must be an instance of `date`')

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`date`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(DateAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is None:
            if not self.none:
                errors.append('Value cannot be `None`')
        elif isinstance(value, date):
            if value.year < 1900 or value.year > 10000:
                errors.append('Year must be between 1900 and 9999')
        else:
            errors.append('Value must be an instance of `date`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize string

        Args:
            value (:obj:`date`): Python representation

        Returns:
            :obj:`float`: simple Python representation
        """
        return value.toordinal() - date(1900, 1, 1).toordinal() + 1.


class TimeAttribute(Attribute):
    """ Time attribute

    Attributes:
        none (:obj:`bool`): if true, the attribute is invalid if its value is None
        default (:obj:`time`): defaul time
    """

    def __init__(self, none=True, default=None, verbose_name='', help='', primary=False, unique=False):
        """
        Args:
            none (:obj:`bool`, optional): if true, the attribute is invalid if its value is None
            default (:obj:`time`, optional): default time
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        super(TimeAttribute, self).__init__(default=default,
                                            verbose_name=verbose_name, help=help,
                                            primary=primary, unique=unique)
        self.none = none

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `time`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if value is None:
            return (value, None)

        if isinstance(value, time):
            return (value, None)

        if isinstance(value, string_types):
            if re.match('^\d{1,2}:\d{1,2}(:\d{1,2})*$', value):
                try:
                    datetime_value = dateutil.parser.parse(value)
                    return (datetime_value.time(), None)
                except ValueError:
                    return (None, InvalidAttribute(self, ['String must be a valid time']))
            else:
                return (None, InvalidAttribute(self, ['String must be a valid time']))

        try:
            int_value = round(float(value) * 24 * 60 * 60)
            if int_value < 0 or int_value > 24 * 60 * 60 - 1:
                return (None, InvalidAttribute(self, ['Number must be a valid time']))

            hour = int(int_value / (60. * 60.))
            minutes = int((int_value - hour * 60. * 60.) / 60.)
            seconds = int(int_value % 60)
            return (time(hour, minutes, seconds), None)
        except ValueError:
            pass

        return (None, 'Value must be an instance of `time`')

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`time`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(TimeAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is None:
            if not self.none:
                errors.append('Value cannot be `None`')
        elif isinstance(value, time):
            if value.microsecond != 0:
                errors.append('Microsecond must be 0')
        else:
            errors.append('Value must be an instance of `time`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize string

        Args:
            value (:obj:`time`): Python representation

        Returns:
            :obj:`float`: simple Python representation
        """
        return (value.hour * 60. * 60. + value.minute * 60. + value.second) / (24. * 60. * 60.)


class DateTimeAttribute(Attribute):
    """ Datetime attribute

    Attributes:
        none (:obj:`bool`): if true, the attribute is invalid if its value is None
        default (:obj:`datetime`): default datetime
    """

    def __init__(self, none=True, default=None, verbose_name='', help='', primary=False, unique=False):
        """
        Args:
            none (:obj:`bool`, optional): if true, the attribute is invalid if its value is None
            default (:obj:`datetime`, optional): default datetime
            verbose_name (:obj:`str`, optional): verbose name
            help (:obj:`str`, optional): help string
            primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        super(DateTimeAttribute, self).__init__(default=default,
                                                verbose_name=verbose_name, help=help,
                                                primary=primary, unique=unique)
        self.none = none

    def clean(self, value):
        """ Convert attribute value into the appropriate type

        Args:
            value (:obj:`object`): value of attribute to clean

        Returns:
            :obj:`tuple` of `datetime`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if value is None:
            return (value, None)

        if isinstance(value, datetime):
            return (value, None)

        if isinstance(value, date):
            return (datetime.combine(value, time(0, 0, 0, 0)), None)

        if isinstance(value, string_types):
            try:
                return (dateutil.parser.parse(value), None)
            except ValueError:
                return (None, InvalidAttribute(self, ['String must be a valid datetime']))

        try:
            float_value = float(value)
            date_int_value = int(float_value)
            time_int_value = round((float_value % 1) * 24 * 60 * 60)

            date_value = date.fromordinal(date_int_value + date(1900, 1, 1).toordinal() - 1)

            if time_int_value < 0 or time_int_value > 24 * 60 * 60 - 1:
                return (None, InvalidAttribute(self, ['Number must be a valid datetime']))
            hour = int(time_int_value / (60. * 60.))
            minutes = int((time_int_value - hour * 60. * 60.) / 60.)
            seconds = int(time_int_value % 60)
            time_value = time(hour, minutes, seconds)

            return (datetime.combine(date_value, time_value), None)
        except ValueError:
            pass

        return (None, 'Value must be an instance of `datetime`')

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`datetime`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(DateTimeAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is None:
            if not self.none:
                errors.append('Value cannot be `None`')
        elif isinstance(value, datetime):
            if value.year < 1900 or value.year > 10000:
                errors.append('Year must be between 1900 and 9999')
            if value.microsecond != 0:
                errors.append('Microsecond must be 0')
        else:
            errors.append('Value must be an instance of `date`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize string

        Args:
            value (:obj:`datetime`): Python representation

        Returns:
            :obj:`float`: simple Python representation
        """
        date_value = value.date()
        time_value = value.time()

        return date_value.toordinal() - date(1900, 1, 1).toordinal() + 1 \
            + (time_value.hour * 60. * 60. + time_value.minute * 60. + time_value.second) / (24. * 60. * 60.)


class RelatedAttribute(Attribute):
    """ Attribute which represents relationships with other objects

    Attributes:
        primary_class (:obj:`class`): parent class
        related_class (:obj:`class`): related class
        related_name (:obj:`str`): name of related attribute on `related_class`
        verbose_related_name (:obj:`str`): verbose related name
        related_default (:obj:`object`): default value of related attribute
    """

    def __init__(self, related_class, related_name='', verbose_name='', verbose_related_name='', help=''):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            help (:obj:`str`, optional): help string
        """

        if not verbose_related_name:
            verbose_related_name = sentencecase(related_name)

        super(RelatedAttribute, self).__init__(verbose_name=verbose_name, help=help,
                                               primary=False, unique=False, unique_case_insensitive=False)
        self.primary_class = None
        self.related_class = related_class
        self.related_name = related_name
        self.verbose_related_name = verbose_related_name
        self.related_default = None

    def get_init_related_value(self, obj):
        """ Get initial related value for attribute

        Args:
            obj (:obj:`object`): object whose attribute is being initialized

        Returns:
            value (:obj:`object`): initial value
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')
        return make_copy(self.related_default)

    def set_related_value(self, obj, new_values):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_values (:obj:`object`): value of the attribute

        Returns:
            :obj:`object`: value of the attribute
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')
        return new_values

    def related_validate(self, obj, value):
        """ Determine if `value` is a valid value of the related attribute

        Args:
            obj (:obj:`Model`): object to validate
            value (:obj:`set`): value to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        return None

    def deserialize(self, value, objects):
        """ Deserialize value

        Args:
            value (:obj:`str`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        return (value, None)


class OneToOneAttribute(RelatedAttribute):
    """ Represents a one-to-one relationship between two types of objects.

    Attributes:
        none (:obj:`bool`): if true, the attribute is invalid if its value is None
        related_none (:obj:`bool`): if true, the related attribute is invalid if its value is `None`
    """

    def __init__(self, related_class, related_name='', none=True, related_none=True, verbose_name='', verbose_related_name='', help=''):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            none (:obj:`bool`, optional): if true, the attribute is invalid if its value is `None`
            related_none (:obj:`bool`, optional): if true, the related attribute is invalid if its value is `None`
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            help (:obj:`str`, optional): help string
        """
        super(OneToOneAttribute, self).__init__(related_class, related_name=related_name,
                                                verbose_name=verbose_name, help=help, verbose_related_name=verbose_related_name)
        self.none = none
        self.related_none = related_none
        self.related_default = None

    def set_value(self, obj, new_value):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_value (:obj:`Model`): new attribute value

        Returns:
            :obj:`Model`: new attribute value
        """
        cur_value = getattr(obj, self.name)
        if cur_value is new_value:
            return new_value

        if new_value and getattr(new_value, self.related_name):
            raise ValueError('Related attribute of `new_value` must be `None`')

        if self.related_name:
            if cur_value:
                cur_value.__setattr__(self.related_name, None, propagate=False)

            if new_value:
                new_value.__setattr__(self.related_name, obj, propagate=False)

        return new_value

    def set_related_value(self, obj, new_value):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_value (:obj:`Model`): value of the attribute

        Returns:
            :obj:`Model`: value of the attribute
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')

        cur_value = getattr(obj, self.related_name)
        if cur_value is new_value:
            return new_value

        if new_value and getattr(new_value, self.name):
            raise ValueError('Attribute of `new_value` must be `None`')

        if cur_value:
            cur_value.__setattr__(self.name, None, propagate=False)

        if new_value:
            new_value.__setattr__(self.name, obj, propagate=False)

        return new_value

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`Model`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(OneToOneAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is None:
            if not self.none:
                errors.append('Value cannot be `None`')
        elif not isinstance(value, self.related_class):
            errors.append('Value must be an instance of "{:s}" or `None`'.format(self.related_class.__name__))
        elif self.related_name:
            if obj is not getattr(value, self.related_name):
                errors.append('Object must be related value')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def related_validate(self, obj, value):
        """ Determine if `value` is a valid value of the related attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`set` of `Model`): value to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(OneToOneAttribute, self).related_validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if self.related_name and value:
            if not isinstance(value, self.primary_class):
                errors.append('Related value must be an instance of "{:s}"'.format(self.primary_class.__name__))
            elif getattr(value, self.name) is not obj:
                errors.append('Object must be related value')

        if errors:
            return InvalidAttribute(self, errors, related=True)
        return None

    def serialize(self, value):
        """ Serialize related object

        Args:
            value (:obj:`Model`): Python representation

        Returns:
            :obj:`str`: simple Python representation
        """
        if value is None:
            return ''

        primary_attr = value.__class__.Meta.primary_attribute
        return primary_attr.serialize(getattr(value, primary_attr.name))

    def deserialize(self, value, objects):
        """ Deserialize value

        Args:
            value (:obj:`str`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if not value:
            return (None, None)

        related_objs = []
        related_classes = chain([self.related_class], get_subclasses(self.related_class))
        for related_class in related_classes:
            if issubclass(related_class, Model) and value in objects[related_class]:
                related_objs.append(objects[related_class][value])

        if len(related_objs) == 0:
            return (None, InvalidAttribute(self, ['Unable to find {} with {}={}'.format(self.related_class.__name__, primary_attr.name, value)]))

        if len(related_objs) == 1:
            return (related_objs[0], None)

        return (None, InvalidAttribute(self, ['Multiple matching objects with primary attribute = {}'.format(value)]))


class ManyToOneAttribute(RelatedAttribute):
    """ Represents a many-to-one relationship between two types of objects. This is analagous to a foreign key relationship in a database.

    Attributes:
        none (:obj:`bool`): if true, the attribute is invalid if its value is None
    """

    def __init__(self, related_class, related_name='', none=True,
                 verbose_name='', verbose_related_name='', help=''):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            none (:obj:`bool`, optional): if true, the attribute is invalid if its value is None
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            help (:obj:`str`, optional): help string
        """
        super(ManyToOneAttribute, self).__init__(related_class, related_name=related_name,
                                                 verbose_name=verbose_name, help=help, verbose_related_name=verbose_related_name)
        self.none = none
        self.related_default = ManyToOneRelatedManager

    def get_init_related_value(self, obj):
        """ Get initial related value for attribute

        Args:
            obj (:obj:`object`): object whose attribute is being initialized

        Returns:
            value (:obj:`object`): initial value
        """
        if not self.related_name:
            raise ValueError('Related property is undefined')
        return ManyToOneRelatedManager(obj, self)

    def set_value(self, obj, new_value):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_value (:obj:`Model`): new attribute value

        Returns:
            :obj:`Model`: new attribute value
        """
        cur_value = getattr(obj, self.name)
        if cur_value is new_value:
            return new_value

        if self.related_name:
            if cur_value:
                cur_related = getattr(cur_value, self.related_name)
                cur_related.remove(obj, propagate=False)

            if new_value:
                new_related = getattr(new_value, self.related_name)
                new_related.add(obj, propagate=False)

        return new_value

    def set_related_value(self, obj, new_values):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_values (:obj:`set`): value of the attribute

        Returns:
            :obj:`set`: value of the attribute
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')

        new_values_copy = list(new_values)

        cur_values = getattr(obj, self.related_name)
        cur_values.clear()
        cur_values.update(new_values_copy)

        return cur_values

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`Model`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(ManyToOneAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is None:
            if not self.none:
                errors.append('Value cannot be `None`')
        elif not isinstance(value, self.related_class):
            errors.append('Value must be an instance of "{:s}" or `None`'.format(self.related_class.__name__))
        elif self.related_name:
            related_value = getattr(value, self.related_name)
            if not isinstance(related_value, set):
                errors.append('Related value must be a set')
            if obj not in related_value:
                errors.append('Object must be in related values')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def related_validate(self, obj, value):
        """ Determine if `value` is a valid value of the related attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`set` of `Model`): value to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(ManyToOneAttribute, self).related_validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if self.related_name:
            if not isinstance(value, set):
                errors.append('Related value must be a set')

            for v in value:
                if not isinstance(v, self.primary_class):
                    errors.append('Related value must be an instance of "{:s}"'.format(self.primary_class.__name__))
                elif getattr(v, self.name) is not obj:
                    errors.append('Object must be related value')

        if errors:
            return InvalidAttribute(self, errors, related=True)
        return None

    def serialize(self, value):
        """ Serialize related object

        Args:
            value (:obj:`Model`): Python representation

        Returns:
            :obj:`str`: simple Python representation
        """
        if value is None:
            return ''

        primary_attr = value.__class__.Meta.primary_attribute
        return primary_attr.serialize(getattr(value, primary_attr.name))

    def deserialize(self, value, objects):
        """ Deserialize value

        Args:
            value (:obj:`str`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if not value:
            return (None, None)

        related_objs = []
        related_classes = chain([self.related_class], get_subclasses(self.related_class))
        for related_class in related_classes:
            if issubclass(related_class, Model) and value in objects[related_class]:
                related_objs.append(objects[related_class][value])

        if len(related_objs) == 0:
            return (None, InvalidAttribute(self, ['Unable to find {} with {}={}'.format(self.related_class.__name__, primary_attr.name, value)]))

        if len(related_objs) == 1:
            return (related_objs[0], None)

        return (None, InvalidAttribute(self, ['Multiple matching objects with primary attribute = {}'.format(value)]))


class OneToManyAttribute(RelatedAttribute):
    """ Represents a one-to-many relationship between two types of objects. This is analagous to a foreign key relationship in a database.

    Attributes:
        related_none (:obj:`bool`): if true, the related attribute is invalid if its value is None
    """

    def __init__(self, related_class, related_name='', related_none=True,
                 verbose_name='', verbose_related_name='', help=''):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            related_none (:obj:`bool`, optional): if true, the related attribute is invalid if its value is None
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            help (:obj:`str`, optional): help string
        """
        super(OneToManyAttribute, self).__init__(related_class, related_name=related_name,
                                                 verbose_name=verbose_name, help=help, verbose_related_name=verbose_related_name)
        self.related_none = related_none
        self.default = OneToManyRelatedManager

    def get_init_value(self, obj):
        """ Get initial value for attribute

        Args:
            obj (:obj:`Model`): object whose attribute is being initialized

        Returns:
            :obj:`object`: initial value
        """
        return OneToManyRelatedManager(obj, self)

    def set_value(self, obj, new_values):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_values (:obj:`set`): value of the attribute

        Returns:
            :obj:`set`: value of the attribute
        """
        new_values_copy = list(new_values)

        cur_values = getattr(obj, self.name)
        cur_values.clear()
        cur_values.update(new_values_copy)

        return cur_values

    def set_related_value(self, obj, new_value):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_value (:obj:`Model`): new attribute value

        Returns:
            :obj:`Model`: new attribute value
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')

        cur_value = getattr(obj, self.related_name)
        if cur_value is new_value:
            return new_value

        if cur_value:
            cur_related = getattr(cur_value, self.name)
            cur_related.remove(obj, propagate=False)

        if new_value:
            new_related = getattr(new_value, self.name)
            new_related.add(obj, propagate=False)

        return new_value

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`set` of `Model`): value to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(OneToManyAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not isinstance(value, set):
            errors.append('Related value must be a set')

        for v in value:
            if not isinstance(v, self.related_class):
                errors.append('Value must be an instance of "{:s}"'.format(self.related_class.__name__))
            elif self.related_name and getattr(v, self.related_name) is not obj:
                errors.append('Object must be related value')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def related_validate(self, obj, value):
        """ Determine if `value` is a valid value of the related attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`Model`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(OneToManyAttribute, self).related_validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if self.related_name:
            if value is None:
                if not self.related_none:
                    errors.append('Value cannot be `None`')
            elif not isinstance(value, self.primary_class):
                errors.append('Value must be an instance of "{:s}" or `None`'.format(self.primary_class.__name__))
            else:
                related_value = getattr(value, self.name)
                if not isinstance(related_value, set):
                    errors.append('Related value must be a set')
                if obj not in related_value:
                    errors.append('Object must be in related values')

        if errors:
            return InvalidAttribute(self, errors, related=True)
        return None

    def serialize(self, value):
        """ Serialize related object

        Args:
            value (:obj:`set` of `Model`): Python representation

        Returns:
            :obj:`str`: simple Python representation
        """

        serialized_vals = []
        for v in value:
            primary_attr = v.__class__.Meta.primary_attribute
            serialized_vals.append(primary_attr.serialize(getattr(v, primary_attr.name)))

        return ', '.join(serialized_vals)

    def deserialize(self, values, objects):
        """ Deserialize value

        Args:
            values (:obj:`object`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if not values:
            return (set(), None)

        deserialized_values = set()
        errors = []
        for value in values.split(','):
            value = value.strip()

            related_objs = []
            related_classes = chain([self.related_class], get_subclasses(self.related_class))
            for related_class in related_classes:
                if issubclass(related_class, Model) and related_class in objects and value in objects[related_class]:
                    related_objs.append(objects[related_class][value])

            if len(related_objs) == 1:
                deserialized_values.add(related_objs[0])
            elif len(related_objs) == 0:
                errors.append('Unable to find {} with {}={}'.format(
                    self.related_class.__name__, self.related_class.Meta.primary_attribute.name, value))
            else:
                errors.append('Multiple matching objects with primary attribute = {}'.format(value))

        if errors:
            return (None, InvalidAttribute(self, errors))
        return (deserialized_values, None)


class ManyToManyAttribute(RelatedAttribute):
    """ Represents a many-to-many relationship between two types of objects. """

    def __init__(self, related_class, related_name='', verbose_name='', verbose_related_name='', help=''):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            help (:obj:`str`, optional): help string
        """
        super(ManyToManyAttribute, self).__init__(related_class, related_name=related_name,
                                                  verbose_name=verbose_name, help=help, verbose_related_name=verbose_related_name)

        self.default = ManyToManyRelatedManager
        self.related_default = ManyToManyRelatedManager

    def get_init_value(self, obj):
        """ Get initial value for attribute

        Args:
            obj (:obj:`Model`): object whose attribute is being initialized

        Returns:
            :obj:`object`: initial value
        """
        return ManyToManyRelatedManager(obj, self, related=False)

    def get_init_related_value(self, obj):
        """ Get initial related value for attribute

        Args:
            obj (:obj:`object`): object whose attribute is being initialized

        Returns:
            value (:obj:`object`): initial value
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')
        return ManyToManyRelatedManager(obj, self, related=True)

    def set_value(self, obj, new_values):
        """ Get value of attribute of object

        Args:
            obj (:obj:`Model`): object
            new_values (:obj:`set`): new attribute value

        Returns:
            :obj:`set`: new attribute value
        """
        new_values_copy = list(new_values)

        cur_values = getattr(obj, self.name)
        cur_values.clear()
        cur_values.update(new_values_copy)

        return cur_values

    def set_related_value(self, obj, new_values):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            new_values (:obj:`set`): value of the attribute

        Returns:
            :obj:`set`: value of the attribute
        """
        if not self.related_name:
            raise ValueError('Related property is not defined')

        new_values_copy = list(new_values)

        cur_values = getattr(obj, self.related_name)
        cur_values.clear()
        cur_values.update(new_values_copy)

        return cur_values

    def validate(self, obj, value):
        """ Determine if `value` is a valid value of the attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`set` of `Model`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(ManyToManyAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not isinstance(value, set):
            errors.append('Value must be a `set`')
        else:
            for v in value:
                if not isinstance(v, self.related_class):
                    errors.append('Value must be a `set` of "{:s}"'.format(self.related_class.__name__))

                if self.related_name:
                    related_v = getattr(v, self.related_name)
                    if not isinstance(related_v, set):
                        errors.append('Related value must be a set')
                    if obj not in related_v:
                        errors.append('Object must be in related values')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def related_validate(self, obj, value):
        """ Determine if `value` is a valid value of the related attribute

        Args:
            obj (:obj:`Model`): object being validated
            value (:obj:`set` of `Model`): value to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(ManyToManyAttribute, self).related_validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if self.related_name:
            if not isinstance(value, set):
                errors.append('Related value must be a set')

            for v in value:
                if not isinstance(v, self.primary_class):
                    errors.append('Related value must be an instance of "{:s}"'.format(self.primary_class.__name__))
                elif obj not in getattr(v, self.name):
                    errors.append('Object must be in related values')

        if errors:
            return InvalidAttribute(self, errors, related=True)
        return None

    def serialize(self, value):
        """ Serialize related object

        Args:
            value (:obj:`set` of `Model`): Python representation

        Returns:
            :obj:`str`: simple Python representation
        """

        serialized_vals = []
        for v in value:
            primary_attr = v.__class__.Meta.primary_attribute
            serialized_vals.append(primary_attr.serialize(getattr(v, primary_attr.name)))

        return ', '.join(serialized_vals)

    def deserialize(self, values, objects):
        """ Deserialize value

        Args:
            values (:obj:`object`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`tuple` of `object`, `InvalidAttribute` or `None`: tuple of cleaned value and cleaning error
        """
        if not values:
            return (set(), None)

        deserialized_values = set()
        errors = []
        for value in values.split(','):
            value = value.strip()

            related_objs = []
            related_classes = chain([self.related_class], get_subclasses(self.related_class))
            for related_class in related_classes:
                if issubclass(related_class, Model) and value in objects[related_class]:
                    related_objs.append(objects[related_class][value])

            if len(related_objs) == 1:
                deserialized_values.add(related_objs[0])
            elif len(related_objs) == 0:
                errors.append('Unable to find {} with {}={}'.format(
                    self.related_class.__name__, primary_attr.name, value))
            else:
                errors.append('Multiple matching objects with primary attribute = {}'.format(value))

        if errors:
            return (None, InvalidAttribute(self, errors))
        return (deserialized_values, None)


class RelatedManager(set):
    """ Represent values and related values of related attributes

    Attributes:
        object (:obj:`Model`): model instance
        attribute (:obj:`Attribute`): attribute
        related (:obj:`bool`): is related attribute
    """

    def __init__(self, object, attribute, related=True):
        """
        Args:
            object (:obj:`Model`): model instance
            attribute (:obj:`Attribute`): attribute
        """
        super(set, self).__init__()
        self.object = object
        self.attribute = attribute
        self.related = related

    def create(self, **kwargs):
        """ Create instance of primary class and add to set

        Args:
            kwargs (:obj:`dict` of `str`: `object`): dictionary of attribute name/value pairs

        Returns:
            :obj:`Model`: created object
        """
        if self.related:
            if self.attribute.name in kwargs:
                raise TypeError("'{}' is an invalid keyword argument for {}.create for {}".format(
                    self.attribute.name, self.__class__.__name__, self.attribute.primary_class.__name__))
            obj = self.attribute.primary_class(**kwargs)

        else:
            if self.attribute.related_name in kwargs:
                raise TypeError("'{}' is an invalid keyword argument for {}.create for {}".format(
                    self.attribute.related_name, self.__class__.__name__, self.attribute.primary_class.__name__))
            obj = self.attribute.related_class(**kwargs)

        self.add(obj)

        return obj

    def discard(self, value):
        """ Remove value from set if value in set

        Args:
            value (:obj:`object`): value
        """
        if value in self:
            self.remove(value)

    def clear(self):
        """ Remove all elements from set """
        for value in list(self):
            self.remove(value)

    def pop(self):
        """ Remove an arbitrary element from the set """
        value = super(set, self).pop()
        self.remove(value, update_set=False)

    def update(self, values):
        """ Add values to set

        Args:
            values (:obj:`set`): values to add to set
        """
        for value in values:
            self.add(value)

    def intersection_update(self, values):
        """ Retain only intersection of set and `values`

        Args:
            values (:obj:`set`): values to intersect with set
        """
        for value in list(self):
            if value not in values:
                self.remove(value)

    def difference_update(self, values):
        """ Retain only values of set not in `values`

        Args:
            values (:obj:`set`): values to difference with set
        """
        for value in list(values):
            if value in self:
                self.remove(value)

    def symmetric_difference_update(self, values):
        """ Retain values in only one of set and `values`

        Args:
            values (:obj:`set`): values to difference with set
        """
        self_copy = set(self)
        values_copy = set(values)

        for value in chain(self_copy, values_copy):
            if value in self_copy:
                if value in values_copy:
                    self.remove(value)
            else:
                self.add(value)

    def get(self, **kwargs):
        """ Get related objects by attribute/value pairs

        Args:
            **kwargs (:obj:`dict` of `str`:`object`): dictionary of attribute name/value pairs to find matching
                objects

        Returns:
            :obj:`Model` or `None`: matching instance of `Model`, or `None` if no matching instance

        Raises:
            :obj:`ValueError`: if multiple matching objects
        """
        matches = self.filter(**kwargs)

        if len(matches) == 0:
            return None

        if len(matches) == 1:
            return matches.pop()

        if len(matches) > 1:
            raise ValueError('Multiple objects match the attribute name/value pair(s)')

    def filter(self, **kwargs):
        """ Get related objects by attribute/value pairs

        Args:
            **kwargs (:obj:`dict` of `str`:`object`): dictionary of attribute name/value pairs to find matching
                objects

        Returns:
            :obj:`set` of `Model`: matching instances of `Model`
        """
        matches = set()

        for obj in self:
            is_match = True
            for attr_name, value in kwargs.items():
                if getattr(obj, attr_name) != value:
                    is_match = False
                    break

            if is_match:
                matches.add(obj)

        return matches


class ManyToOneRelatedManager(RelatedManager):
    """ Represent values of related attributes """

    def __init__(self, object, attribute):
        """
        Args:
            object (:obj:`Model`): model instance
            attribute (:obj:`Attribute`): attribute
        """
        super(ManyToOneRelatedManager, self).__init__(object, attribute, related=True)

    def add(self, value, propagate=True):
        """ Add value to set

        Args:
            value (:obj:`object`): value
            propagate (:obj:`bool`, optional): propagate change to related attribute
        """
        if value in self:
            return

        super(ManyToOneRelatedManager, self).add(value)
        if propagate:
            value.__setattr__(self.attribute.name, self.object, propagate=True)

    def remove(self, value, update_set=True, propagate=True):
        """ Remove value from set

        Args:
            value (:obj:`object`): value
            propagate (:obj:`bool`, optional): propagate change to related attribute
        """
        if update_set:
            super(ManyToOneRelatedManager, self).remove(value)
        if propagate:
            value.__setattr__(self.attribute.name, None, propagate=False)


class OneToManyRelatedManager(RelatedManager):
    """ Represent values of related attributes """

    def __init__(self, object, attribute):
        """
        Args:
            object (:obj:`Model`): model instance
            attribute (:obj:`Attribute`): attribute
        """
        super(OneToManyRelatedManager, self).__init__(object, attribute, related=False)

    def add(self, value, propagate=True):
        """ Add value to set

        Args:
            value (:obj:`object`): value
            propagate (:obj:`bool`, optional): propagate change to related attribute
        """
        if value in self:
            return

        super(OneToManyRelatedManager, self).add(value)
        if propagate:
            value.__setattr__(self.attribute.related_name, self.object, propagate=True)

    def remove(self, value, update_set=True, propagate=True):
        """ Remove value from set

        Args:
            value (:obj:`object`): value
            propagate (:obj:`bool`, optional): propagate change to related attribute
        """
        if update_set:
            super(OneToManyRelatedManager, self).remove(value)
        if propagate:
            value.__setattr__(self.attribute.related_name, None, propagate=False)


class ManyToManyRelatedManager(RelatedManager):
    """ Represent values and related values of related attributes """

    def add(self, value, propagate=True):
        """ Add value to set

        Args:
            value (:obj:`object`): value
            propagate (:obj:`bool`, optional): propagate change to related attribute
        """
        if value in self:
            return

        super(ManyToManyRelatedManager, self).add(value)
        if propagate:
            if self.related:
                getattr(value, self.attribute.name).add(self.object, propagate=False)
            else:
                getattr(value, self.attribute.related_name).add(self.object, propagate=False)

    def remove(self, value, update_set=True, propagate=True):
        """ Remove value from set

        Args:
            value (:obj:`object`): value
            update_set (:obj:`bool`, optional): update set
            propagate (:obj:`bool`, optional): propagate change to related attribute
        """
        if update_set:
            super(ManyToManyRelatedManager, self).remove(value)
        if propagate:
            if self.related:
                getattr(value, self.attribute.name).remove(self.object, propagate=False)
            else:
                getattr(value, self.attribute.related_name).remove(self.object, propagate=False)


class InvalidObjectSet(object):
    """ Represents a list of invalid objects and their errors

    Attributes:
        objects (:obj:`list`): list of invalid objects
        models (:obj:`list` of `InvalidModel`): list of invalid models
    """

    def __init__(self, objects, models):
        """
        Args:
            objects (:obj:`list` of `InvalidObject`): list of invalid objects
            models (:obj:`list` of `InvalidModel`): list of invalid models
        """
        self.objects = objects or []
        self.models = models or []

    def get_object_errors_by_model(self):
        """ Get object errors grouped by models

        Returns:
            :obj:`dict` of `Model`: `list` of `InvalidObject`: dictionary of object errors, grouped by model
        """

        obj_by_model = {}
        for obj in self.objects:
            if obj.object.__class__ not in obj_by_model:
                obj_by_model[obj.object.__class__] = []
            obj_by_model[obj.object.__class__].append(obj)

        return obj_by_model

    def get_model_errors_by_model(self):
        """ Get object errors grouped by models

        Returns:
            :obj:`dict` of `Model`: `InvalidModel`: dictionary of model errors, grouped by model
        """
        return {model.model: model for model in self.models}

    def __str__(self):
        """ Get string representation of errors

        Returns:
            :obj:`str`: string representation of errors
        """
        str = ''

        obj_errs = self.get_object_errors_by_model()
        mdl_errs = self.get_model_errors_by_model()

        models = set(obj_errs.keys())
        models.update(set(mdl_errs.keys()))
        models = natsorted(models, attrgetter('__name__'), alg=ns.IGNORECASE)

        for model in models:
            str += '{}:\n'.format(model.__name__)

            if model in obj_errs:
                errs = natsorted(obj_errs[model], key=lambda x: x.object.get_primary_attribute(), alg=ns.IGNORECASE)
                for obj_err in errs:
                    str += '  ' + obj_err.__str__().replace('\n', '\n  ').rstrip(' ')

            if model in mdl_errs:
                str += mdl_errs[model].__str__().replace('\n', '\n  ').rstrip(' ')

        return str


class InvalidModel(object):
    """ Represents an invalid model, such as a model with an attribute that doesn't have unique values

    Attributes:
        model (:obj:`class`): `Model` class
        attributes (:obj:`list` of `InvalidAttribute`): list of invalid attributes and their errors
    """

    def __init__(self, model, attributes):
        """
        Args:
            model (:obj:`class`): `Model` class
            attributes (:obj:`list` of `InvalidAttribute`): list of invalid attributes and their errors
        """
        self.model = model
        self.attributes = attributes

    def __str__(self):
        """ Get string representation of errors

        Returns:
            :obj:`str`: string representation of errors
        """
        str = ''
        for attr in self.attributes:
            str += attr.__str__()
        return str


class InvalidObject(object):
    """ Represents an invalid object and its errors

    Attributes:
        object (:obj:`object`): invalid object
        attributes (:obj:`list` of `InvalidAttribute`): list of invalid attributes and their errors
    """

    def __init__(self, object, attributes):
        """
        Args:
            object (:obj:`Model`): invalid object
            attributes (:obj:`list` of `InvalidAttribute`): list of invalid attributes and their errors
        """
        self.object = object
        self.attributes = attributes

    def __str__(self):
        """ Get string representation of errors

        Returns:
            :obj:`str`: string representation of errors
        """
        str = '{}:\n'.format(self.object.get_primary_attribute())
        for attr in self.attributes:
            str += '  ' + attr.__str__().replace('\n', '\n  ').rstrip(' ')
        return str


class InvalidAttribute(object):
    """ Represents an invalid attribute and its errors

    Attributes:
        attribute (:obj:`Attribute`): invalid attribute
        message (:obj:`list` of `str`): list of error message
        related (:obj:`bool`): indicates if error is about value or related value
    """

    def __init__(self, attribute, messages, related=False):
        """
        Args:
            attribute (:obj:`Attribute`): invalid attribute
            message (:obj:`list` of `str`): list of error message
            related (:obj:`bool`, optional): indicates if error is about value or related value
        """
        self.attribute = attribute
        self.messages = messages
        self.related = related

    def __str__(self):
        """ Get string representation of errors

        Returns:
            :obj:`str`: string representation of errors
        """
        if self.related:
            str = '{}:\n'.format(self.attribute.related_name)
        else:
            str = '{}:\n'.format(self.attribute.name)

        for msg in self.messages:
            str += '  {}\n'.format(msg)

        return str


def get_model(name):
    """ Get model with name `name`

    Args:
        name (:obj:`str`): name

    Returns:
        :obj:`class`: model class
    """
    for model in get_subclasses(Model):
        if name == model.__module__ + '.' + model.__name__:
            return model

    return None


class Validator(object):
    """ Engine to validate sets of objects """

    def run(self, objects):
        """ Validate a list of objects and return their errors

        Args:
            object (:obj:`list` of `Model`): list of objects

        Returns:
            :obj:`InvalidObjectSet` or `None`: list of invalid objects/models and their errors
        """
        error = self.clean(objects)
        if error:
            return error
        return self.validate(objects)

    def clean(self, objects):
        """ Clean a list of objects and return their errors

        Args:
            object (:obj:`list` of `Model`): list of objects

        Returns:
            :obj:`InvalidObjectSet` or `None`: list of invalid objects/models and their errors
        """

        object_errors = []
        for obj in objects:
            error = obj.clean()
            if error:
                object_errors.append(error)

        if object_errors:
            return InvalidObjectSet(object_errors, None)

        return None

    def validate(self, objects):
        """ Validate a list of objects and return their errors

        Args:
            object (:obj:`list` of `Model`): list of objects

        Returns:
            :obj:`InvalidObjectSet` or `None`: list of invalid objects/models and their errors
        """

        # validate individual objects
        object_errors = []
        for obj in objects:
            error = obj.validate()
            if error:
                object_errors.append(error)

        # group objects by class
        objects_by_class = {}
        for obj in objects:
            for cls in obj.__class__.Meta.inheritance:
                if cls not in objects_by_class:
                    objects_by_class[cls] = []
                objects_by_class[cls].append(obj)

        # validate collections of objects of each Model type
        model_errors = []
        for cls, cls_objects in objects_by_class.items():
            error = cls.validate_unique(cls_objects)
            if error:
                model_errors.append(error)

        # return errors
        if object_errors or model_errors:
            return InvalidObjectSet(object_errors, model_errors)

        return None
