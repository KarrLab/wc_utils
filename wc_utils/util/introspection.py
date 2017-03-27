""" Introspection utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-03-27
:Copyright: 2017, Karr Lab
:License: MIT
"""

from qualname import qualname
import inspect

def get_class_that_defined_function(function):
    """ Get the class which defines a function

    Args:
        function (:obj:`function`): function

    Returns:
        :obj:`type`: class that defines the function 

    From: http://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545
    """

    if inspect.ismethod(function):
        for cls in inspect.getmro(function.__self__.__class__):
            if cls.__dict__.get(function.__name__) is function:
                return cls
        function = function.__func__  # fallback to __qualname__ parsing

    if inspect.isfunction(function):
        cls = getattr(inspect.getmodule(function),
                      qualname(function).split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls

    return None  # not required since None would have been implicitly returned anyway
