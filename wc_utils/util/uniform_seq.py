""" Generate an infinite sequence of evenly spaced values

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2019-12-11
:Copyright: 2019, Karr Lab
:License: MIT
"""

from decimal import Decimal, getcontext
import collections

from wc_utils.config.core import get_config
UNIFORM_SEQ_PRECISION = get_config()['wc_utils']['misc']['uniform_seq_precision']


class UniformSequence(collections.abc.Iterator):
    """ Generate an infinite sequence of evenly spaced values, especially for non-integral step sizes

    The start and step size must be an integer or a float whose mantissa must contain no more
    than `UNIFORM_SEQ_PRECISION` digits.
    Avoids floating-point roundoff errors by using a :obj:`Decimal` to represent the step size.

    Attributes:
        _start (:obj:`Decimal`): starting point of the sequence
        _step (:obj:`Decimal`): step size for the sequence
        _num_steps (:obj:`int`): number of steps taken in the sequence
    """

    def __init__(self, start, step):
        """ Initialize a :obj:`UniformSequence`

        Args:
            start (:obj:`float`): starting point of the sequence
            step (:obj:`float`): step size for the sequence

        Raises:
            :obj:`ValueError`: if the step size is 0, NaN, or infinite, or
                if the precision in `start` or `step` exceeds `UNIFORM_SEQ_PRECISION`
        """
        self._start = Decimal(start)
        getcontext().prec = UNIFORM_SEQ_PRECISION
        self._step = Decimal(step)
        if not self._step.is_normal():
            raise ValueError(f"UniformSequence: step={step} can't be 0, NaN, infinite, or subnormal")

        # start and step truncated to the Decimal precision must be within 1E-(UNIFORM_SEQ_PRECISION+1)
        # of start and step, respectively
        atol = 10**-(UNIFORM_SEQ_PRECISION+1)
        if atol < abs(float(str(self._start * 1)) - start):
            raise ValueError(f"UniformSequence: precision in start={start} exceeds UNIFORM_SEQ_PRECISION "
                             f"threshold={UNIFORM_SEQ_PRECISION}")
        if atol < abs(float(str(self._step * 1)) - step):
            raise ValueError(f"UniformSequence: precision in step={step} exceeds UNIFORM_SEQ_PRECISION "
                             f"threshold={UNIFORM_SEQ_PRECISION}")
        self._num_steps = 0

    def __iter__(self):
        """ Get this :obj:`UniformSequence`

        Returns:
            :obj:`UniformSequence`: this :obj:`UniformSequence`
        """
        return self

    def __next__(self):
        """ Get next value in the sequence

        Returns:
            :obj:`float`: next value in this :obj:`UniformSequence`
        """
        next_value = self._start + self._num_steps * self._step
        self._num_steps += 1
        if next_value.is_zero():
            return 0.
        return float(next_value)

    # todo: support scientific notation in truncate() so that sequences like this work
    # ((0, 1E-11), (0, .1E-10, .2E-10, .3E-10, .4E-10, .5E-10, .6E-10, .7E-10, .8E-10, .9E-10)),
    @staticmethod
    def truncate(value):
        """ Truncate a uniform sequence value into fixed-point notation for output

        Raise an exception if truncation loses precision.

        Raises:
            :obj:`StopIteration`: if the truncated value does not equal `value`
        """
        truncated_value = f'{value:.{UNIFORM_SEQ_PRECISION}f}'
        if float(truncated_value) != value:
            raise StopIteration(f'UniformSequence: truncation error:\n'
                                f'value: {value}; truncated_value: {truncated_value} '
                                f'num digits precision: {UNIFORM_SEQ_PRECISION}; ')
        return truncated_value
