""" A decorator that solves the problem of default parameter values that become global data structures.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-01
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from functools import wraps

# a map from parameter name prefix or suffix to data type
prefix_suffix_types = { 'list':'list', 'dict':'dict', 'set':'set'}
def typed( param ):
    ''' Indicate whether the `param` indicates a data type

    Args:
        param (:obj:`str`): a variable name whose prefix or suffix might indicate its data type,
        which would be one of 'list', 'dict', or 'set'

    Returns:
        :obj:`boolean`: True if `param` indicates a data type
    '''
    return (param.endswith( tuple( map( lambda x: '_'+x, prefix_suffix_types.keys()) ) )or
        param.startswith( tuple( map( lambda x: x+'_', prefix_suffix_types.keys()) ) ) )

def none_to_empty( param, value ):
    ''' If value is None, return an empty data structure whose type is indicated by param

    Args:
        param (:obj:`str`): a variable name whose prefix or suffix indicates its data type
        value (:obj:`obj`): a value, which might be None

    Returns:
        :obj:`obj`: value unmodified, or if value is None, an empty data structure whose
        type is indicated by param
    '''
    if value is None:
        for key in prefix_suffix_types.keys():
            if param.endswith( '_'+key ) or param.startswith( key+'_' ):
                return eval( prefix_suffix_types[key] + '()' )
    return value

def default_mutable_params(mutable_args):
    """A function or method decorator that handles mutable optional parameters.

    Optional parameters with mutable default values like d and l in "def f( d={}, l=[])" have
    the awkward behavior that a global mutable data strcture is created when the function (or
    method) is defined, that references to the parameter access this data structure, and that
    all calls to the function which do not provide the parameter refer to this data
    structure. This differs from the semantics naive Python programmers expect, which is that
    calls that don't provide the parameter initialize it as an empty data structure.

    Somewhat surprisingly, the Python Language Reference
    recommends (https://docs.python.org/3.5/reference/compound_stmts.html#function-definitions)
    that this behavior be fixed by defining the
    default value for such optional parameters as None, and setting the parameter as empty
    data structure if it is not provided (or is provided as None). However, this is cumbersome,
    especially if the function contains a large number of such parameters.

    This decorator transforms optional parameters whose default values None into mutable data
    structures of the appropriate type. The parameters must have names whose prefix or suffix
    indicates their data type (as in so-called Hungarian or rudder notation). The mutable
    parameters are provided as a list to the decorator. The decorated function uses None as
    default values for these parameters. Calls to the decorated function replace optional
    parameters whose value is None with the appropriate empty data structure. For example,
    consider::

        @default_mutable_params( ['d_dict', 'list_l', 's_set'] )
        def test3( a, d_dict=None, list_l=None, s_set=None, l2=[4] )

    The call::

        test3( 1, d_dict={3}, list_l=None, s_set=None, l2=None )

    will be transformed into::

        test3( 1, d_dict={3}, list_l=[], s_set=set(), l2=None )

    where the values of ``list_l`` and ``s_set`` are local variables.

    Args:
        mutable_args (:obj:`list`): list of optional parameters whose default values are mutable
        data structure.

    Returns:
        :obj:`type`: description

    Raises:
        :obj:`ValueError`: if an argument to @default_mutable_params does not indicate
        the type of its aggregate data structure

    TODO(Arthur): An alternative way to define default_params_decorator and avoid the need to
    add the type to the name of each parameter and select parameters for the decorator,
    would be to copy the target function's signature as the decorator's argument, parse the
    signature with compile(), and then use the parse's AST to determine the optional parameters
    with default datastructures, and their data types.
    """
    def default_params_decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            for mutable in mutable_args:
                if not typed(mutable):
                    raise ValueError("Arguments to @default_mutable_params must indicate their type in "
                        "the name prefix or suffix, but '{}' does not.".format(mutable))
                if mutable in list(kwargs.keys()):
                    kwargs[mutable] = none_to_empty(mutable, kwargs[mutable])
                else:
                    kwargs[mutable] = none_to_empty(mutable, None)
            return func(*args, **kwargs)
        return func_wrapper
    return default_params_decorator

