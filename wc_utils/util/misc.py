""" Miscellaneous utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-05
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import six
import sys
import socket

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
    """Obtain the most qualified class name available for `obj`.

    Since references to classes cannot be sent in messages that leave an address space,
    use the most qualified class name available to compare class values across address spaces.
    Fully qualified class names are available for Python >= 3.3.

    Args:
        obj (:obj:`class`): an object, which may be a class.

    Returns:
        :obj:`str`: the most qualified class name available for `obj`.
    """
    if isinstance(obj, six.class_types):
        cls = obj
    else:
        cls = obj.__class__

    if (3, 3) <= sys.version_info:
        return cls.__module__ + '.' + cls.__qualname__
    else:
        return cls.__module__ + '.' + cls.__name__  # pragma: no cover # old Python


def round_direct(value, precision=2):
    '''Convert `value` to rounded string with appended sign indicating the rounding direction.

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
    '''
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
    except OSError:
        pass
    return False


class OrderableNoneType(object):
    """ Type than can be used for sorting in Python 3 in place of :obj:`None` """

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


OrderableNone = OrderableNoneType()
# Object than can be used for sorting in Python 3 in place of :obj:`None`


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
