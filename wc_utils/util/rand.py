"""Random number generator utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-07
:Copyright: 2016, Karr Lab
:License: MIT
"""

from random import Random
from numpy import random as numpy_random
from six import integer_types
from wc_utils.util.types import TypesUtil
import math
import numpy as np


class ReproducibleRandom(object):
    """A source of reproducible random numbers.

    A static, singleton class that can provide random numbers that are reproducible 
    or non-reproducible. 'Reproducible' will produce identical sequences of random
    values for independent executions of a deterministic application that uses this class,
    thereby making the application reproducible. This enables comparison of multiple independent
    simulator executions that use different algorithms and/or inputs.

    Naturally, non-reproducible random numbers are randomly independent. 

    ReproducibleRandom provides both reproducible sequences of random numbers and independent, 
    reproducible random number streams. These can be seeded by a built-in seed 
    (used by the 'reproducible' argument to init()) or a single random seed provided 
    to the 'seed' argument to init().

    If ReproducibleRandom is initialized without either of these seeds, then it
    will generate random numbers and streams seeded by the randomness source used by numpy's
    RandomState().

    Attributes:
        built_in_seed (int): a built-in RNG seed, to provide reproducibility when no
            external seed is provided
        _private_PRNG (PRNG): used to generate random values
        RNG_generator (numpy RandomState()): a PRNG for generating additional, independent
            random number streams
    """

    _built_in_seed = 17
    _private_PRNG = None
    _RNG_generator = None

    @staticmethod
    def init(reproducible=False, seed=None):
        """Initialize ReproducibleRandom.

        Args:
            reproducible (boolean): if set, use the hard-coded, built-in PRNG seed
            seed (a hashable object): if reproducible is not set, a seed that seeds
                all random numbers and random streams provided by ReproducibleRandom.
        """
        if reproducible:
            ReproducibleRandom._private_PRNG = numpy_random.RandomState(
                ReproducibleRandom._built_in_seed)
        elif seed != None:
            ReproducibleRandom._private_PRNG = numpy_random.RandomState(seed)
        else:
            ReproducibleRandom._private_PRNG = numpy_random.RandomState()
        ReproducibleRandom._RNG_generator = numpy_random.RandomState(
            ReproducibleRandom._private_PRNG.randint(np.iinfo(np.uint32).max))

    @staticmethod
    def _check_that_init_was_called():
        """Checks whether ReproducibleRandom.init() was called.

        Raises:
            ValueError: if init() was not called
        """
        if ReproducibleRandom._private_PRNG == None:
            raise ValueError("Error: ReproducibleRandom: ReproducibleRandom.init() must "
                             "be called before calling other ReproducibleRandom methods.")

    @staticmethod
    def get_numpy_random_state():
        """Provide a new numpy RandomState() instance.

        The RandomState() instance can be used by threads or to initialize
        concurrent processes which cannot share a random number stream because
        they execute asynchronously.

        Returns:
            numpy RandomState(): A new `RandomState()` instance. If ReproducibleRandom.init() was
            called to make reproducible random numbers, then the RandomState() instance will do so.

        Raises:
            ValueError: if init() was not called
        """
        ReproducibleRandom._check_that_init_was_called()
        return numpy_random.RandomState(ReproducibleRandom._RNG_generator.randint(np.iinfo(np.uint32).max))

    @staticmethod
    def get_numpy_random():
        """Provide a reference to a singleton numpy RandomState() instance.

        The output of this RandomState() instance is not reproducible across threads or
        other non-deterministically asynchronous components, but it can shared by components
        of a deterministic sequential program.

        Returns:
            numpy RandomState(): If ReproducibleRandom.init() was called to make reproducible
            random numbers, then the RandomState() instance will do so.

        Raises:
            ValueError: if init() was not called
        """
        ReproducibleRandom._check_that_init_was_called()
        return ReproducibleRandom._private_PRNG

class StochasticRound( object ):
    """Stochastically round floating point values.
    Attributes:
        RNG: A Random instance, initialized on creation of a StochasticRound.
    """

    def __init__( self, rng=None ):
        """Initialize a StochasticRound.
        Args:
            rng (numpy random number generator, optional): to use a deterministic sequence of
            random numbers in round() provide an RNG initialized with a deterministically selected
            seed. Otherwise some system-dependent randomness source will be used to initialize a
            numpy random number generator. See the documentation of `numpy.random`.
        Raises:
            ValueError if rng is not a numpy_random.RandomState
        """
        if rng is not None:
            if not isinstance( rng, numpy_random.RandomState ):
                raise ValueError( "rng must be a numpy RandomState." )
            self.RNG = rng
        else:
            self.RNG = numpy_random.RandomState( )

    def stochastic_uniform_rounder( self, x ):
        """Stochastically round a floating point value.
        A float is rounded to one of the two nearest integers. The mean of the rounded values for a
        set of floats converges to the mean of the floats. This is achieved by making
            P[round x down] = 1 - (x - floor(x) ), and
            P[round x up] = 1 - P[round x down].
        This avoids the bias that would arise from always using floor() or ceiling(),
        especially with small populations.
        Args:
            x (float): a value to be stochastically rounded.
        Returns:
            int: a stochastic round of x.
        """
        return math.floor(x + self.RNG.random_sample())

    def random_round( self, x ):
        '''Randomly round a fractional part of 0.5

        Round a float to the closest integer. If the fractional part of `x` is 0.5, randomly
        round `x` up or down. This avoids rounding bias.
        See http://www.clivemaxfield.com/diycalculator/sp-round.shtml#A15

        Args:
            x (:obj:`float`): a value to be randomly rounded

        Returns:
            :obj:`int`: a random round of `x`
        '''
        fraction = x - math.floor( x )
        if fraction < 0.5:
            return math.floor( x )
        elif 0.5 < fraction:
            return math.ceil( x )
        elif self.RNG.randint(2):
            return math.floor( x )
        else:
            return math.ceil( x )

    def poisson_round( self, x ):
        '''Poisson round a float

        Round a float to the closest integer. 

        Args:
            x (float): a value to be poission rounded
        Returns:
            int: a random round of x
        '''
        pass


def validate_random_state(random_state):
    """ Validates a random state

    Args:
        random_state (:obj:`obj`): random state

    Raises:
        :obj:`InvalidRandomStateException`: if `random_state` is not valid
    """

    if not TypesUtil.is_iterable(random_state):
        raise InvalidRandomStateException('Random state must be a tuple')

    if len(random_state) != 5:
        raise InvalidRandomStateException('Random state must have length 5')

    if random_state[0] != 'MT19937':
        raise InvalidRandomStateException('Random random_state[0] must be equal to "MT19937"')

    if not TypesUtil.is_iterable(random_state[1]) or len(random_state[1]) != 624:
        raise InvalidRandomStateException(
            'Random number generator random_state[1] must be an array of length 624 of unsigned ints')
    for r in random_state[1]:
        if not isinstance(r, (integer_types, np.uint32)):
            raise InvalidRandomStateException(
                'Random number generator random_state[1] must be an array of length 624 of unsigned ints')

    if not isinstance(random_state[2], int):
        raise InvalidRandomStateException('Random number generator random_state[2] must be an int')

    if not isinstance(random_state[3], int):
        raise InvalidRandomStateException('Random number generator random_state[3] must be an int')

    if not isinstance(random_state[4], float):
        raise InvalidRandomStateException('Random number generator random_state[3] must be an float')

    return True


class InvalidRandomStateException(Exception):
    ''' An exception for invalid random states '''
    pass
    