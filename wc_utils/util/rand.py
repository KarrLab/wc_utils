"""Random number generator utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-07
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from numpy import random as numpy_random
from six import integer_types
from wc_utils.util.types import is_iterable
import math
import numpy as np
import wc_utils


class RandomStateManager(object):
    """ Manager for singleton of :obj:`numpy.random.RandomState` """

    _random_state = None
    #:obj:`numpy.random.RandomState`: singleton random state

    @classmethod
    def initialize(cls, seed=None):
        """ Constructs the singleton random state, if it doesn't already exist
        and seeds the random state.

        Args:
            seed (:obj:`int`): random number generator seed
        """
        if not cls._random_state:
            cls._random_state = RandomState(seed=seed)
        if seed is None:
            config = wc_utils.config.core.get_config()['wc_utils']['random']
            seed = config['seed']
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


class RandomState(np.random.RandomState):
    """ Enhanced random state with additional random methods for
    * Rounding
    """

    def round(self, x, method='binomial'):
        """Stochastically round a floating point value.

        Args:
            x (:obj:`float`): a value to be rounded.
            method (:obj:`str`, optional): the type of rounding to use. The default is 'binomial'.

        Returns:
            :obj:`int`: rounded value of `x`.

        Raises:
            :obj:`Exception`: if `method` is not one of the valid types: 'binomial', 'midpoint',
                'poisson', and 'quadratic'.
        """
        if method == 'binomial':
            return self.round_binomial(x)
        elif method == 'midpoint':
            return self.round_midpoint(x)
        elif method == 'poisson':
            return self.round_poisson(x)
        elif method == 'quadratic':
            return self.round_quadratic(x)
        else:
            raise Exception('Undefined rounding method: {}'.format(method))

    def round_binomial(self, x):
        """Stochastically round a float.

        Randomly round a float to one of the two nearest integers. This is achieved by making

            P[round `x` to floor(`x`)] = f = 1 - (`x` - floor(`x`)), and
            P[round `x` to ceil(`x`)] = 1 - f.

        This avoids the bias that would arise from always using `floor` or `ceil`,
        especially with small populations.
        The mean of the rounded values for a set of floats converges to the mean of the floats.

        Args:
            x (:obj:`float`): a value to be rounded.

        Returns:
            :obj:`int`: rounded value of `x`.
        """
        return math.floor(x + self.random_sample())

    def round_midpoint(self, x):
        '''Round to the closest integer; if the fractional part of `x` is 0.5, randomly round up or down.

        Round a float to the closest integer. If the fractional part of `x` is 0.5, randomly
        round `x` up or down. This avoids rounding bias if the distribution of `x` is not uniform.
        See http://www.clivemaxfield.com/diycalculator/sp-round.shtml#A15

        Args:
            x (:obj:`float`): a value to be rounded

        Returns:
            :obj:`int`: rounded value of `x`
        '''
        fraction = x - math.floor(x)
        if fraction < 0.5:
            return math.floor(x)
        elif 0.5 < fraction:
            return math.ceil(x)
        elif self.randint(2):
            return math.floor(x)
        else:
            return math.ceil(x)

    def round_poisson(self, x):
        """Stochastically round a floating point value by sampling from a poisson distribution.

        A sample of Poisson(x) is provided, the domain of which is the integers in [0,inf). It
        is not symmetric about a fractional part of 0.5.

        Args:
            x (:obj:`float`): a value to be rounded.

        Returns:
            :obj:`int`: rounded value of `x`.
        """
        return self.poisson(x)

    def round_quadratic(self, x):
        """Stochastically round a float, with a quadratic bias towards the closest integer.

        Stochastically round a float. Rounding is non-linearly biased towards the closest integer.
        This rounding behaves symmetrically about 0.5. Its expected value when rounding a
        unif(0,1) random variable is 0.5.

        Args:
            x (:obj:`float`): a value to be rounded.

        Returns:
            :obj:`int`: rounded value of `x`.
        """
        return math.floor(x + self.std())

    def std(self):
        """Sample a symmetric triangular distribution.

        The pdf of symmetric triangular distribution is

            4x       for 0<=x<.5,
            4(1-x)   for .5<=x<=1, and
            0        elsewhere.

        See https://en.wikipedia.org/wiki/Triangular_distribution.

        Returns:
            :obj:`float`: a sample from a symmetric triangular distribution.
        """
        return (self.random_sample()+self.random_sample())/2

    def ltd(self):
        """Sample a left triangular distribution.

        The pdf of ltd is f(x) = 2(1-x) for 0<=x<=1, and 0 elsewhere.

        Returns:
            :obj:`float`: a sample from a left triangular distribution.
        """
        return abs(self.random_sample()-self.random_sample())

    def rtd(self):
        """Sample a right triangular distribution.

        The pdf of rtd is f(x) = 2x for 0<=x<=1, and 0 elsewhere.

        Returns:
            :obj:`float`: a sample from a right triangular distribution.
        """
        return 1-self.ltd()

def validate_random_state(random_state):
    """ Validates a random state

    Args:
        random_state (:obj:`obj`): random state

    Raises:
        :obj:`InvalidRandomStateException`: if `random_state` is not valid
    """

    if not is_iterable(random_state):
        raise InvalidRandomStateException('Random state must be a tuple')

    if len(random_state) != 5:
        raise InvalidRandomStateException('Random state must have length 5')

    if random_state[0] != 'MT19937':
        raise InvalidRandomStateException('Random random_state[0] must be equal to "MT19937"')

    if not is_iterable(random_state[1]) or len(random_state[1]) != 624:
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
