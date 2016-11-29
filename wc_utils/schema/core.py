""" Schema

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from collections import OrderedDict
from copy import copy, deepcopy
from enum import Enum
from itertools import chain
from math import isnan
from natsort import natsort_keygen, ns
from six import with_metaclass
from stringcase import sentencecase
from wc_utils.util.types import get_subclasses, get_superclasses
import inflect
import re


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

            Meta.attributes_order = []
            for base in bases:
                if issubclass(base, Model):
                    for attr_name in base.Meta.attributes_order:
                        if attr_name not in Meta.attributes_order:
                            Meta.attributes_order.append(attr_name)
            Meta.attributes_order = tuple(Meta.attributes_order)

        # call super class method
        cls = super(ModelMeta, metacls).__new__(metacls, name, bases, namespace)

        # Initialize meta data
        metacls.init_inheritance(cls)

        metacls.init_attributes(cls)

        metacls.init_primary_attribute(cls)

        cls.Meta.related_attributes = {}
        for model in get_subclasses(Model):
            metacls.init_related_attributes(model)

        metacls.init_attributes_order(cls)

        metacls.init_verbose_names(cls)

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
                if isinstance(attr.related_class, str):
                    related_class_name = attr.related_class
                    if '.' not in related_class_name:
                        related_class_name = cls.__module__ + '.' + related_class_name

                    related_class = get_model(related_class_name)
                    if related_class:
                        attr.related_class = related_class

                # setup related attributes on related classes
                if attr.name in cls.__dict__ and attr.related_name and issubclass(attr.related_class, Model):
                    related_classes = chain([attr.related_class], get_subclasses(attr.related_class))
                    for related_class in related_classes:
                        # check that related class has primary attributes
                        if not related_class.Meta.primary_attribute:
                            raise ValueError('Related class {} must have a primary attribute'.format(
                                related_class.__name__))

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
        primary_attributes = [attr for attr in cls.Meta.attributes.values() if attr.is_primary]

        if len(primary_attributes) == 0:
            cls.Meta.primary_attribute = None

        elif len(primary_attributes) == 1:
            cls.Meta.primary_attribute = primary_attributes[0]

        else:
            raise ValueError('Model {} cannot have more than one primary attribute'.format(cls.__name__))

    def init_attributes_order(cls):
        """ Initialize the order in which the attributes should be printed across Excel columns """
        ordered_attributes = list(cls.Meta.attributes_order or ())

        unordered_attributes = set()
        for base in cls.Meta.inheritance:
            for attr_name in base.__dict__.keys():
                if isinstance(getattr(base, attr_name), Attribute) and attr_name not in ordered_attributes:
                    unordered_attributes.add(attr_name)

        unordered_attributes = list(unordered_attributes)
        unordered_attributes.sort(key=natsort_keygen(alg=ns.IGNORECASE))

        cls.Meta.attributes_order = tuple(ordered_attributes + unordered_attributes)

    def init_verbose_names(cls):
        """ Initialize the singular and plural verbose names of a model """
        if not cls.Meta.verbose_name:
            cls.Meta.verbose_name = sentencecase(cls.__name__)

        if not cls.Meta.verbose_name_plural:
            inflect_engine = inflect.engine()
            cls.Meta.verbose_name_plural = inflect_engine.plural(cls.Meta.verbose_name)


class Model(with_metaclass(ModelMeta, object)):
    """ Base object model """

    class Meta(object):
        """ Meta data for :class:`Model`

        Attributes:
            attributes (:obj:`set` of `Attribute`): attributes
            related_attributes(:obj:`set` of `Attribute`): attributes declared in related objects            
            primary_attribute (:obj:`Attribute`): attributes with `is_primary`=True
            attributes_order (:obj:`tuple` of `str`): tuple of attribute names, in the order in which they should be displayed
            verbose_name (:obj:`str`): verbose name to refer to a instance of the model
            verbose_name_plural (:obj:`str`): plural verbose name to refer to instances of the model
        """
        attributes = None
        related_attributes = None
        primary_attribute = None
        attributes_order = ()
        verbose_name = ''
        verbose_name_plural = ''
        num_frozen_columns = 1
        inheritance = None

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs (:obj:`dict`, optional): dictionary of keyword arguments with keys equal to the names of the model attributes
        """

        """ check that related classes of attributes are defined """
        for attr_name, attr in self.Meta.attributes.items():
            if isinstance(attr, RelatedAttribute) and not issubclass(attr.related_class, Model):
                raise ValueError('Related class {} of {}.{} must be defined'.format(
                    attr.related_class, attr.primary_class.__name__, attr_name))

        """ initialize attributes """
        # attributes
        for attr_name, attr in self.Meta.attributes.items():
            setattr(self, attr_name, attr.default)

        for attr_name, val in kwargs.items():
            if attr_name not in self.Meta.attributes:
                raise TypeError("'{:s}' is an invalid keyword argument for this function".format(attr_name))
            setattr(self, attr_name, val)

        # related attributes
        for attr_name, attr in self.Meta.related_attributes.items():
            setattr(self, '_' + attr_name, copy(attr.related_default))

    def __setattr__(self, attr_name, value):
        """ Set value of attribute

        Args:
            attr_name (:obj:`str`): attribute name
            value (:obj:`object`): attribute value
        """
        if attr_name in self.Meta.attributes:
            attr = self.Meta.attributes[attr_name]
            if isinstance(attr, RelatedAttribute):
                if hasattr(self, attr_name) and getattr(self, attr_name) is not attr:
                    cur_value = getattr(self, attr_name)
                else:
                    cur_value = None
                attr.related_set(self, cur_value, value)

        elif attr_name in self.Meta.related_attributes:
            raise ValueError('Related attribute "{}" cannot be set'.format(attr_name))

        super(Model, self).__setattr__(attr_name, value)

    def __getattr__(self, attr_name):
        """ Get value of attribute

        Args:
            attr_name (:obj:`str`): attribute name

        Returns:
            :obj:`object`: attribute value
        """

        if attr_name in self.Meta.related_attributes:
            return getattr(self, '_' + attr_name)
        raise AttributeError('"{}" does not have attribute "{}"'.format(self.__class__.__name__, attr_name))

    def __eq__(self, other):
        """ Determine if two objects are semantically equal

        Args:
            other (:obj:`object`): object to compare

        Returns:
            :obj:`bool`: `True` if objects are semantically equal, else `False`
        """
        if self is other:
            return True

        if not self.__class__ is other.__class__:
            return False

        for attr_name in self.Meta.attributes.keys():
            if getattr(self, attr_name) != getattr(other, attr_name):
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

    def get_primary_attribute(self):
        """ Get values of primary attribute

        Returns:
            :obj:`object`: values of primary attribute
        """
        if self.__class__.Meta.primary_attribute:
            return getattr(self, self.__class__.Meta.primary_attribute.name)

        return None

    def get_related(self, _related_objects=None):
        """ Get all related objects

        Args:
            _related_objects (:obj:`set` of `Model`): preliminary set of related objects

        Returns:
            :obj:`set` of `Model`: related objects
        """
        if _related_objects is None:
            _related_objects = set()

        for attr in self.__class__.Meta.attributes.values():
            if isinstance(attr, RelatedAttribute):
                value = getattr(self, attr.name)

                if isinstance(value, set):
                    for v in value:
                        if v not in _related_objects:
                            _related_objects.add(v)
                            v.get_related(_related_objects)
                else:
                    if value not in _related_objects:
                        _related_objects.add(value)
                        value.get_related(_related_objects)

        for attr in self.__class__.Meta.related_attributes.values():
            value = getattr(self, attr.related_name)

            if isinstance(value, set):
                for v in value:
                    if v not in _related_objects:
                        _related_objects.add(v)
                        v.get_related(_related_objects)
            else:
                if value not in _related_objects:
                    _related_objects.add(value)
                    value.get_related(_related_objects)

        return _related_objects

    def validate(self):
        """ Determine if all of the object's attributes are valid

        Args:
            related (:obj:`bool`): if true, validate all recursively related objects

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
            error = attr.related_validate(self, getattr(self, attr_name))
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
            :obj:`InvalidModel`: list of invalid attributes and their errors
        """
        errors = []
        for attr_name, attr in cls.Meta.attributes.items():
            if attr.is_unique:
                vals = set()
                rep_vals = set()
                for obj in objects:
                    val = getattr(obj, attr_name)
                    if val in vals:
                        rep_vals.add(val)
                    else:
                        vals.add(val)

                if rep_vals:
                    message = 'Values must be unique. The following values are repeated:\n- ' + '\n- '.join(rep_vals)
                errors.append(InvalidAttribute(attr, [message]))

        if errors:
            return InvalidModel(cls, errors)
        return None


class Attribute(object):
    """ Model attribute

    Attributes:        
        name (:obj:`str`): name
        default (:obj:`object`): default value
        verbose_name (:obj:`str`): verbose_name
        is_primary (:obj:`bool`): indicate if attribute is primary attribute
        is_unique (:obj:`bool`): indicate if attribute value must be unique
    """

    def __init__(self, default=None, verbose_name='', is_primary=False, is_unique=False):
        """
        Args:
            default (:obj:`object`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        self.name = None
        self.default = default
        self.verbose_name = verbose_name
        self.is_primary = is_primary
        self.is_unique = is_unique

    def validate(self, obj, value):
        """ Determine if `value` is a validate value of the attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        return None

    def serialize(self, value):
        """ Serialize value

        Args:
            value (:obj:`object`): Python representation

        Returns:
            :obj:`str`: string representation
        """
        return str(value)

    def deserialize(self, value):
        """ Deserialize value

        Args:
            value (:obj:`object`): String representation

        Returns:
            :obj:`object`: Python representation
        """
        return value


class EnumAttribute(Attribute):
    """ Enumeration attribute

    Attributes:
        enum_class (:obj:`type`): subclass of `Enum`
    """

    def __init__(self, enum_class, default=None, verbose_name='', is_primary=False, is_unique=False):
        """
        Args:
            enum_class (:obj:`type`): subclass of `Enum`
            default (:obj:`object`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        if not issubclass(enum_class, Enum):
            raise ValueError('`enum_class` must be an subclass of `Enum`')
        if default is not None and not isinstance(default, enum_class):
            raise ValueError('Default must be None or an instance of `enum_class`')

        super(EnumAttribute, self).__init__(default=default,
                                            verbose_name=verbose_name, is_primary=is_primary, is_unique=is_unique)

        self.enum_class = enum_class

    def validate(self, obj, value):
        """ Determine if `value` is a validate value of the attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(EnumAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if isinstance(value, str):
            if value in self.enum_class.__members__:
                value = self.enum_class[value]
                setattr(obj, self.name, value)
            else:
                errors.append('Value must be convertible to an instance of {}'.format(self.enum_class.__name__))

        elif isinstance(value, (int, float)):
            try:
                value = self.enum_class(value)
                setattr(obj, self.name, value)
            except ValueError:
                errors.append('Value must be convertible to an instance of {}'.format(self.enum_class.__name__))

        elif not isinstance(value, self.enum_class):
            errors.append('Value must be an instance of `{}`'.format(self.enum_class.__name__))

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize enumeration

        Args:
            value (:obj:`Enum`): Python representation

        Returns:
            :obj:`str`: string representation
        """
        return value.name

    def deserialize(self, value):
        """ Deserialize enumeration

        Args:
            value (:obj:`str`): string representation

        Returns:
            :obj:`Enum`: Python representation
        """
        return self.enum_class[value]


class FloatAttribute(Attribute):
    """ Float attribute

    Attributes:
        min (:obj:`float`): minimum value
        max (:obj:`float`): maximum value
        default (:obj:`float`, optional): default value
    """

    def __init__(self, min=float('nan'), max=float('nan'), default=float('nan'), verbose_name='', is_primary=False, is_unique=False):
        """
        Args:
            min (:obj:`float`, optional): minimum value
            max (:obj:`float`, optional): maximum value
            default (:obj:`float`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        min = float(min)
        max = float(max)
        default = float(default)
        if not isnan(min) and not isnan(max) and max < min:
            raise ValueError('max must be at least min')

        super(FloatAttribute, self).__init__(default=default,
                                             verbose_name=verbose_name, is_primary=is_primary, is_unique=is_unique)

        self.min = min
        self.max = max

    def validate(self, obj, value):
        """ Determine if `value` is a validate value of the attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(FloatAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        try:
            value = float(value)
            setattr(obj, self.name, value)

            if not isnan(self.min):
                if isnan(value):
                    errors.append('Value cannot be nan')
                elif value < self.min:
                    errors.append('Value must be at least {:f}'.format(self.min))

            if not isnan(self.max):
                if isnan(value):
                    errors.append('Value cannot be nan')
                elif value > self.max:
                    errors.append('Value must be at most {:f}'.format(self.max))

        except ValueError:
            errors.append('Value must be an instance of `float`')

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize float

        Args:
            value (:obj:`float`): Python representation

        Returns:
            :obj:`str`: string representation
        """
        if isnan(value):
            return ''
        return str(value)

    def deserialize(self, value):
        """ Deserialize string

        Args:
            value (:obj:`str` or None): String representation

        Returns:
            :obj:`float`: Python representation
        """
        return float(value or 'nan')


class StringAttribute(Attribute):
    """ String attribute

    Attributes:
        min_length (:obj:`int`): minimum length
        max_length (:obj:`int`): maximum length
        default (:obj:`str`, optional): default value
    """

    def __init__(self, min_length=0, max_length=None, default='', verbose_name='', is_primary=False, is_unique=False):
        """
        Args:
            min_length (:obj:`int`, optional): minimum length
            max_length (:obj:`int`, optional): maximum length
            default (:obj:`str`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """

        if not isinstance(min_length, int) or min_length < 0:
            raise ValueError('min_length must be a non-negative integer')
        if (max_length is not None) and (not isinstance(max_length, int) or max_length < 0):
            raise ValueError('max_length must be None or a non-negative integer')
        if not isinstance(default, str):
            raise ValueError('Default must be a string')

        super(StringAttribute, self).__init__(default=default,
                                              verbose_name=verbose_name, is_primary=is_primary, is_unique=is_unique)

        self.min_length = min_length
        self.max_length = max_length

    def validate(self, obj, value):
        """ Determine if `value` is a validate value of the attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(StringAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not isinstance(value, str):
            errors.append('Value must be an instance of `str`')
        else:
            if len(value) < self.min_length:
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
            :obj:`str`: string representation
        """
        return value

    def deserialize(self, value):
        """ Deserialize string

        Args:
            value (:obj:`str` or None): String representation

        Returns:
            :obj:`str`: Python representation
        """
        return value or ''


class RegexAttribute(StringAttribute):
    """ Regular expression attribute

    Attributes:
        pattern (:obj:`str`): regular expression pattern
        flags (:obj:`int`): regular expression flags
    """

    def __init__(self, pattern, flags=None, min_length=0, max_length=None, default='', verbose_name='', is_primary=False, is_unique=False):
        """
        Args:
            pattern (:obj:`str`): regular expression pattern
            flags (:obj:`int`, optional): regular expression flags
            min_length (:obj:`int`, optional): minimum length
            max_length (:obj:`int`, optional): maximum length
            default (:obj:`str`, optional): default value
            verbose_name (:obj:`str`, optional): verbose name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """

        super(RegexAttribute, self).__init__(min_length=min_length, max_length=max_length,
                                             default=default, verbose_name=verbose_name, is_primary=is_primary, is_unique=is_unique)
        self.pattern = pattern
        self.flags = flags

    def validate(self, obj, value):
        """ Determine if `value` is a validate value of the attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(RegexAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not re.match(self.pattern, value, flags=self.flags):
            errors.append('Value must match pattern: {:s}'.format(self.pattern))

        if errors:
            return InvalidAttribute(self, errors)
        return None


class RelatedAttribute(Attribute):
    """ Attribute which represents relationships with other objects

    Attributes:
        primary_class (:obj:`class`): parent class
        related_class (:obj:`class`): related class
        related_name (:obj:`str`): name of related attribute on `related_class`
        verbose_related_name (:obj:`str`): verbose related name
    """

    def __init__(self, related_class, related_name='', verbose_name='', verbose_related_name='', is_primary=False, is_unique=False):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """

        super(RelatedAttribute, self).__init__(verbose_name=verbose_name, is_primary=is_primary, is_unique=is_unique)
        self.primary_class = None
        self.related_class = related_class
        self.related_name = related_name
        self.verbose_related_name = verbose_related_name
        self.related_default = None

    def related_set(self, obj, cur_related_obj, new_related_obj):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            cur_related_obj (:obj:`object`): current value of the attribute
            new_related_obj (:obj:`object`): new value of the attribute
        """
        pass

    def related_validate(self, obj, value):
        """ Determine if `value` is a validate value of the related attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        return None


class ManyToOneAttribute(RelatedAttribute):
    """ Represents a many-to-one relationship between two types of objects. This is analagous to a foreign key relationship in a database.

    Attributes:
        is_none (:obj:`bool`): if true, the attribute is invalid if its value is None
    """

    def __init__(self, related_class, related_name='', is_none=False, verbose_name='', verbose_related_name='', is_primary=False, is_unique=False):
        """
        Args:
            related_class (:obj:`class`): related class
            related_name (:obj:`str`, optional): name of related attribute on `related_class`
            is_none (:obj:`bool`, optional): if true, the attribute is invalid if its value is None
            verbose_name (:obj:`str`, optional): verbose name
            verbose_related_name (:obj:`str`, optional): verbose related name
            is_primary (:obj:`bool`, optional): indicate if attribute is primary attribute
            is_unique (:obj:`bool`, optional): indicate if attribute value must be unique
        """
        super(ManyToOneAttribute, self).__init__(related_class, related_name=related_name,
                                                 verbose_name=verbose_name, verbose_related_name=verbose_related_name,
                                                 is_primary=is_primary, is_unique=is_unique)
        self.related_default = set()
        self.is_none = is_none

    def related_set(self, obj, cur_related_obj, new_related_obj):
        """ Update the values of the related attributes of the attribute

        Args:
            obj (:obj:`object`): object whose attribute should be set
            cur_related_obj (:obj:`object`): current value of the attribute
            new_related_obj (:obj:`object`): new value of the attribute
        """
        super(ManyToOneAttribute, self).related_set(obj, cur_related_obj, new_related_obj)

        if self.related_name:
            if cur_related_obj:
                cur_related_value = getattr(cur_related_obj, '_' + self.related_name)
                cur_related_value.remove(obj)

            if new_related_obj:
                if not hasattr(new_related_obj, '_' + self.related_name):
                    raise ValueError('Related object must have attribute "_{}"'.format(self.related_name))

                new_related_value = getattr(new_related_obj, '_' + self.related_name)
                new_related_value.add(obj)

    def validate(self, obj, value):
        """ Determine if `value` is a validate value of the attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(ManyToOneAttribute, self).validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if value is None:
            if not self.is_none:
                errors.append('Value cannot be none')

        else:
            if not isinstance(value, self.related_class):
                errors.append('Value must be an instance of "{:s}'.format(self.related_class))
            elif self.related_name:
                related_value = getattr(value, '_' + self.related_name)

                if not isinstance(related_value, set):
                    errors.append('Related value must be a set')

                elif obj not in getattr(value, '_' + self.related_name):
                    errors.append('Object must be a member of the related property "_{:s}"'.format(self.related_name))

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def related_validate(self, obj, value):
        """ Determine if `value` is a validate value of the related attribute

        Args:
            obj (:obj:`object`): object being validated
            value (:obj:`value`): value of attribute to validate

        Returns:
            :obj:`InvalidAttribute` or None: None if attribute is valid, other return list of errors as an instance of `InvalidAttribute`
        """
        errors = super(ManyToOneAttribute, self).related_validate(obj, value)
        if errors:
            errors = errors.messages
        else:
            errors = []

        if not isinstance(value, set):
            errors.append('Related value must be a set')

        for v in value:
            if not isinstance(v, self.primary_class):
                errors.append('Related value must be an instance of "{:s}"'.format(self.primary_class.__name__))

        if errors:
            return InvalidAttribute(self, errors)
        return None

    def serialize(self, value):
        """ Serialize related object

        Args:
            value (:obj:`Model`): Python representation

        Returns:
            :obj:`str`: string representation
        """
        primary_attr = value.__class__.Meta.primary_attribute
        return primary_attr.serialize(getattr(value, primary_attr.name))

    def deserialize(self, value, objects):
        """ Deserialize value

        Args:
            value (:obj:`object`): String representation
            objects (:obj:`dict`): dictionary of objects, grouped by model

        Returns:
            :obj:`Model`: Python representation
        """
        if not value:
            return None

        related_objs = []
        related_classes = chain([self.related_class], get_subclasses(self.related_class))
        for related_class in related_classes:
            if issubclass(related_class, Model):
                primary_attr = self.related_class.Meta.primary_attribute
                for obj in objects[related_class]:
                    if primary_attr.serialize(getattr(obj, primary_attr.name)) == value:
                        related_objs.append(obj)

        if len(related_objs) == 0:
            raise ValueError('Unable to find {} with {}={}'.format(
                self.related_class.__name__, primary_attr.name, value))

        if len(related_objs) == 1:
            return related_objs[0]

        raise ValueError('Multiple matching objects with primary attribute = {}'.format(value))


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


class InvalidAttribute(object):
    """ Represents an invalid attribute and its errors

    Attributes:
        attribute (:obj:`Attribute`): invalid attribute
        message (:obj:`list` of `str`): list of error message
    """

    def __init__(self, attribute, messages):
        """
        Args:
            attribute (:obj:`Attribute`): invalid attribute
            message (:obj:`list` of `str`): list of error message
        """
        self.attribute = attribute
        self.messages = messages


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


def validate_objects(objects):
    """ Validate a list of objects and return their errors

    Args:
        object (:obj:`list` of `Model`): list of objects

    Returns:
        :obj:`InvalidObjectSet`: list of invalid objects/models and their errors
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