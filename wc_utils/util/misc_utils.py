""" Miscellaneous utilities.

:Author: Jonathan Karr, karr@mssm.edu
:Date: 3/22/2016
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 10/05/2016
:Copyright: 2016, Karr Lab
:License: MIT
"""

import numpy as np

def nanminimum(x, y):
    return np.where(np.logical_or(np.isnan(y), np.logical_and(x <= y, np.logical_not(np.isnan(x)))), x, y)
    
def nanmaximum(x, y):
    return np.where(np.logical_or(np.isnan(y), np.logical_and(x >= y, np.logical_not(np.isnan(x)))), x, y)

def compare_name_with_class( a_name, a_class ):
    """Compares class name with the type of a_class.
    
    Used by SimulationObject instances in handle_event() to compare the event message type 
    field against event message types.
    
    Returns:
        True if the the name of class a_class is a_name.
    """
    return a_name == a_class.__name__

def dict_2_key_sorted_str( d ):
    '''Provide a string representation of a dictionary sorted by key.
    '''
    if d == None:
        return '{}'
    else:
        return '{' + ", ".join("%r: %r" % (key, d[key]) for key in sorted(d)) + '}'
