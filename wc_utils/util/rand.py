"""Random number generator utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-07
:Copyright: 2016, Karr Lab
:License: MIT
"""

from numpy import random as numpy_random
from six import integer_types
from wc_utils.util.types import TypesUtil
import math
import numpy as np


class RandomStateManager(object):
    """ Manager for singleton of :obj:`numpy.random.RandomState` """

    DEFAULT_SEED = 117
    #:obj:`int`: default seed for the random state

    _random_state = None
    #:obj:'numpy.random.RandomState': singleton random state

    @classmethod
    def initialize(cls, seed=None):
        """ Constructs the singleton random state, if it doesn't already exist
        and seeds the random state. 

        Args:
            seed (:obj:`int`): random number generator seed
        """
        if not cls._random_state:
            cls._random_state = np.random.RandomState(seed=seed)
        if seed is None:
            seed = cls.DEFAULT_SEED
        cls._random_state.seed(seed)

    @classmethod
    def instance(cls):
        """ Returns the single random state

        Returns:
            :obj:`numpy.random.RandomState`: random state
        """
        if not cls._random_state:
            cls.initialize()
        return cls._random_state


class StochasticRound(object):
    """Stochastically round floating point values.
    Attributes:
        RNG: A Random instance, initialized on creation of a StochasticRound.
    """

    def __init__(self, rng=None):
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
            if not isinstance(rng, numpy_random.RandomState):
                raise ValueError("rng must be a numpy RandomState.")
            self.RNG = rng
        else:
            self.RNG = numpy_random.RandomState()

    def round(self, x):
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

    def random_round(self, x):
        '''Randomly round a fractional part of 0.5

        Round a float to the closest integer. If the fractional part of `x` is 0.5, randomly
        round `x` up or down. This avoids rounding bias.

        Args:
            x (:obj:`float`): a value to be randomly rounded

        Returns:
            :obj:`int`: a random round of `x`
        '''
        fraction = x - math.floor(x)
        if fraction < 0.5:
            return math.floor(x)
        elif 0.5 < fraction:
            return math.ceil(x)
        elif self.RNG.randint(2):
            return math.floor(x)
        else:
            return math.ceil(x)


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
