""" Miscellaneous utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-05
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from fractions import Fraction
import collections.abc
import copy
import dataclasses
import math
import os
import pickle
import socket
import sys


def isclass(cls, cls_info):
    """Compares a class with classes in `cls_info`.

    Args:
        cls (:obj:`str`): class
        cls_info (:obj:`class`, :obj:`type`, or :obj:`tuple` of classes and types): class, type, or
            tuple of classes and types

    Returns:
        :obj:`bool`: True if one of the classes in `cls_info` is `cls`.
    """
    return isclass_by_name(most_qual_cls_name(cls), cls_info)


def isclass_by_name(cls_name, cls_info):
    """Compares a class name with the names of the classes in `cls_info`.

    Args:
        cls_name (:obj:`str`): class name
        cls_info (:obj:`class`, :obj:`type`, or :obj:`tuple` of classes and types): class, type, or
            tuple of classes and types

    Returns:
        :obj:`bool`: True if one of the classes in `cls_info` has name `cls_name`.
    """
    if not isinstance(cls_info, tuple):
        cls_info = (cls_info,)

    for a_cls_info in cls_info:
        if isinstance(a_cls_info, tuple):
            if isclass_by_name(cls_name, a_cls_info):
                return True
        elif cls_name == most_qual_cls_name(a_cls_info):
            return True

    return False


def most_qual_cls_name(obj):
    """ Obtain the most qualified class name available for `obj`.

    Since references to classes cannot be sent in messages that leave an address space,
    use the most qualified class name available to compare class values across address spaces.
    Fully qualified class names are available for Python >= 3.3.

    Args:
        obj (:obj:`class`): an object, which may be a class.

    Returns:
        :obj:`str`: the most qualified class name available for `obj`.
    """
    if isinstance(obj, type):
        cls = obj
    else:
        cls = obj.__class__

    if (3, 3) <= sys.version_info:
        return cls.__module__ + '.' + cls.__qualname__
    else:
        return cls.__module__ + '.' + cls.__name__  # pragma: no cover # old Python


def round_direct(value, precision=2):
    """ Convert `value` to rounded string with appended sign indicating the rounding direction.

    Append '+' to indicate that `value` has been rounded down, and '-' to indicate rounding up.
    For example, 
    round_direct(3.01, 2) == '3.01'
    round_direct(3.01, 1) == '3.0+'
    round_direct(2.99, 1) == '3.0-'

    This function helps display simulation times that have been slightly increased or decreased to
    control order execution.

    Args:
        value (float): the value to round.
        precision (int): the precision with which to round `value`.

    Returns:
        str: `value` rounded to `precision` places, followed by a sign indicating rounding direction.
    """
    if round(value, precision) == value:
        return str(round(value, precision))
    elif round(value, precision) < value:
        return '{}+'.format(round(value, precision))
    else:   # value < round(value, precision)
        return '{}-'.format(round(value, precision))


def quote(s):
    """ Enclose a string that contains spaces in single quotes, 'like this'

    Args:
        s (:obj:`str`): a string

    Returns:
        :obj:`str`: a string
    """
    if ' ' in s:
        return "'{}'".format(s)
    else:
        return s


def obj_to_str(obj, attrs):
    """ Provide a string representation of an object

    Args:
        obj (:obj:`object`): an object
        attrs (:obj:`collections.abc.Iterator`): the names of attributes in `obj` to represent

    Returns:
        :obj:`str`: a string
    """
    rv = ['\nClass: ' + obj.__class__.__name__]
    for attr in attrs:
        if hasattr(obj, attr):
            rv.append("{}: {}".format(attr, str(getattr(obj, attr))))
        else:
            rv.append("{}: --not defined--".format(attr))
    return '\n'.join(rv)


def as_dict(obj):
    """ Provide a dictionary representation of `obj`

    `obj` must define an attribute called `ATTRIBUTES` which iterates over the attributes that
    should be included in the representation.

    Recursively computes `as_dict()` on nested objects that define `ATTRIBUTES`. Warning: calling
    `as_dict` on cyclic networks of objects will cause infinite recursion and stack overflow.

    Returns:
        :obj:`dict`: a representation of `obj` mapping attribute names to values, nested for nested
            objects

    Raises:
        :obj:`ValueError`: `obj` does not define an attribute called `ATTRIBUTES`
    """
    if not hasattr(obj, 'ATTRIBUTES'):
        raise ValueError('obj must define the attribute ATTRIBUTES')
    d = {}
    for attr in obj.ATTRIBUTES:
        contained_obj = getattr(obj, attr)
        if hasattr(contained_obj, 'ATTRIBUTES'):
            d[attr] = as_dict(contained_obj)
        else:
            d[attr] = getattr(obj, attr)
    return d


def internet_connected():
    """ Determine whether the Internet is connected

    Returns:
        :obj:`bool`: return `True` if the internet (actually www.google.com) is accessible, `False` otherwise
    """
    try:
        # connect to the host -- tells us if the host is actually reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError: # pragma: no cover
        pass
    return False    # pragma: no cover


class OrderableNoneType(object):
    """ Type that can be used for sorting in Python 3 in place of :obj:`None` """

    def __lt__(self, other):
        return (other is not self) and (other is not None)

    def __le__(self, other):
        return True

    def __eq__(self, other):
        return (other is self) or (other is None)

    def __ge__(self, other):
        return (other is self) or (other is None)

    def __gt__(self, other):
        return False


# Object that can be used for sorting in Python 3 in place of :obj:`None`
OrderableNone = OrderableNoneType()


def geometric_iterator(min, max, factor):
    """ Create a geometic sequence

    Generate the sequence `min`, `min`*`factor`, `min`*`factor`**2, ..., stopping at the first
    element greater then or equal to `max`.

    Args:
        min (:obj:`float`): first and smallest element of the geometic sequence
        max (:obj:`float`): largest element of the geometic sequence
        factor (:obj:`float`): multiplicative factor between sequence entries

    Returns:
        :obj:`iterator` of :obj:`float`: the geometic sequence

    Raises:
        :obj:`ValueError`: if `min` <= 0, or
            if `max` < `min`, or
            if `factor` <= 1
    """
    if not 0 < min:
        raise ValueError(f'min = {min}; 0 < min is required')
    if max < min:
        raise ValueError(f'min = {min} and max = {max}; min <= max is required')
    if factor <= 1:
        raise ValueError(f'factor = {factor}; 1 < factor is required')
    sequence_value = min
    while sequence_value < max or math.isclose(sequence_value, max, rel_tol=1E-14):
        yield sequence_value
        sequence_value *= factor


class DFSMAcceptor(object):
    """ Deterministic finite state machine (DFSM) that accepts sequences which move from the start to the end state

    A data-driven finite state machine (finite-state automaton). States and messages can be any
    hashable type.

    Attributes:
        start_state (:obj:`object`): a DFSM's start state
        accepting_state (:obj:`object`): a DFSM must be in this state to accept a message sequence
        transitions_dict (:obj:`dict`): transitions, a map state -> message -> next state
        state (:obj:`object`): a DFSM's current state
    """

    # acceptance fails
    FAIL = 'fail'
    # acceptance succeeds
    ACCEPT = 'accept'

    def __init__(self, start_state, accepting_state, transitions):
        """
        Args:
            start_state (:obj:`object`): a DFSM's start state
            accepting_state (:obj:`object`): a DFSM must be in this state to accept a message sequence
            transitions (:obj:`iterator` of `tuple`): transitions, an iterator of
                (state, message, next state) tuples

        Raises:
            :obj:`ValueError`: if `transitions` contains redundant transitions, or if no transitions
                out of `start_state` are provided
        """
        self.start_state = start_state
        self.accepting_state = accepting_state
        self.transitions_dict = {}
        for state, transition_message, new_state in transitions:
            if state not in self.transitions_dict:
                self.transitions_dict[state] = {}
            if transition_message in self.transitions_dict[state]:
                raise ValueError("'{}' already a transition from '{}'".format(transition_message,
                    state))
            self.transitions_dict[state][transition_message] = new_state
        if start_state not in self.transitions_dict:
            raise ValueError("no transitions available from start state '{}'".format(start_state))
        self.reset()

    def reset(self):
        """ Reset a DFSM to it's start state
        """
        self.state = self.start_state

    def get_state(self):
        """ Get a DFSM's state
        """
        return self.state

    def exec_transition(self, message):
        """ Execute one DFSM state transition

        Args:
            message (:obj:`object`): a message that might transition the DFSM to another state

        Returns:
            :obj:`object`: returns `DFSMAcceptor.FAIL` if `message` does not transition the DFSM to
                another state; otherwise returns `None`
        """
        if message not in self.transitions_dict[self.state]:
            return DFSMAcceptor.FAIL
        self.state = self.transitions_dict[self.state][message]

    def run(self, transition_messages):
        """ Execute one DFSM state transition

        Args:
            transition_messages (:obj:`iterator` of `object`): an iterator that provides messages that
                might transition a DFSM from its `start_state` to its `accepting_state`

        Returns:
            :obj:`object`: returns `DFSMAcceptor.FAIL` if `transition_messages` do not transition the
                DFSM to from its `start_state` to its `accepting_state`; otherwise returns `DFSMAcceptor.ACCEPT`
        """
        self.reset()
        for transition_message in transition_messages:
            rv = self.exec_transition(transition_message)
            if rv == DFSMAcceptor.FAIL:
                return DFSMAcceptor.FAIL
        if self.state == self.accepting_state:
            return DFSMAcceptor.ACCEPT
        return DFSMAcceptor.FAIL


class EnhancedDataClass(object):
    """ A mixin that enhances dataclasses

    Attributes:
        LIKELY_INITIAL_VOWEL_SOUNDS (:obj:`set` of :obj:`str`): initial letters of words that will
            be preceeded by 'an'
        DO_NOT_PICKLE (:obj:`set` of :obj:`str`): fields in a dataclass that cannot be pickled
    """

    LIKELY_INITIAL_VOWEL_SOUNDS = {'a', 'e', 'i', 'o', 'u'}
    DO_NOT_PICKLE = set()

    def validate_dataclass_type(self, attr_name):
        """ Validate the type of an attribute in a dataclass instance

        Args:
            attr_name (:obj:`str`): the name of the attribute to validate

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`ValueError`: if `attr_name` is not the name of a field
            :obj:`TypeError`: if attribute `attr_name` does not have the right type
        """

        fields_map = {field.name: field for field in dataclasses.fields(self)}
        if attr_name not in fields_map:
            raise ValueError(f"'{attr_name}' must be a field in {self.__class__.__name__}")

        # validate type
        field = fields_map[attr_name]
        attr = getattr(self, field.name)

        # place the right article before a type name, approximately
        single_article = 'a'
        if field.type.__name__[0].lower() in self.LIKELY_INITIAL_VOWEL_SOUNDS:
            single_article = 'an'

        # accept int inputs to float fields
        if isinstance(attr, int) and field.type is float:
            attr = float(attr)
            setattr(self, field.name, attr)

        # dataclasses._MISSING_TYPE is the value used for default if no default is provided
        if 'dataclasses._MISSING_TYPE' in str(field.default):
            if not isinstance(attr, field.type):
                raise TypeError(f"{field.name} ('{attr}') must be {single_article} {field.type.__name__}")
        else:
            if (field.default is None and attr is not None) or field.default is not None:
                if not isinstance(attr, field.type):
                    raise TypeError(f"{field.name} ('{attr}') must be {single_article} {field.type.__name__}")

    def validate_dataclass_types(self):
        """ Validate the types of all attributes in a dataclass instance

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`error_type`: if an attribute does not have the right type
        """

        # validate types
        for field in dataclasses.fields(self):
            self.validate_dataclass_type(field.name)

    def __setattr__(self, name, value):
        """ Validate a dataclass attribute when it is changed """
        object.__setattr__(self, name, value)
        self.validate_dataclass_type(name)

    def prepare_to_pickle(self):
        """ Provide a copy of this instance that can be pickled; recursively calls nested :obj:`EnhancedDataClass`\ s

        Some objects, such as functions, cannot be pickled. Replace the value of these attributes with :obj:`None`.

        Returns:
            :obj:`SimulationConfig`: a copy of `self` that can be pickled
        """
        to_pickle = copy.deepcopy(self)
        for field in dataclasses.fields(self):
            attr = getattr(self, field.name)
            if field.name in self.DO_NOT_PICKLE:
                setattr(to_pickle, field.name, None)
            elif isinstance(attr, EnhancedDataClass):
                setattr(to_pickle, field.name, attr.prepare_to_pickle())
        return to_pickle

    @classmethod
    def write_dataclass(cls, dataclass, dirname):
        """ Save an `EnhancedDataClass` object to the directory `dirname`

        Args:
            dataclass (:obj:`EnhancedDataClass`): an `EnhancedDataClass` instance
            dirname (:obj:`str`): directory for holding the dataclass

        Raises:
            :obj:`ValueError`: if a dataclass has already been written to `dirname`
        """

        pathname = cls.get_pathname(dirname)
        if os.path.isfile(pathname):
            raise ValueError(f"'{pathname}' already exists")

        with open(pathname, 'wb') as file:
            pickle.dump(dataclass.prepare_to_pickle(), file)

    @classmethod
    def read_dataclass(cls, dirname):
        """ Read an `EnhancedDataClass` object from the directory `dirname`

        Args:
            dirname (:obj:`str`): directory for holding the dataclass

        Returns:
            :obj:`EnhancedDataClass`: an `EnhancedDataClass` object
        """

        pathname = cls.get_pathname(dirname)

        # load and return this EnhancedDataClass
        with open(pathname, 'rb') as file:
            return pickle.load(file)

    @staticmethod
    def get_pathname(dirname):
        """ Get the pathname for a pickled :obj:`EnhancedDataClass` object stored in directory `dirname`

        Subclasses of :obj:`EnhancedDataClass` that read or write files must override this method.

        Args:
            dirname (:obj:`str`): directory for holding the dataclass

        Returns:
            :obj:`str`: pathname for the :obj:`EnhancedDataClass`
        """

        raise ValueError(f"subclasses of EnhancedDataClass that read or write files must define get_pathname method")
        return os.path.join(dirname, 'filename goes here')  # pragma: no cover
