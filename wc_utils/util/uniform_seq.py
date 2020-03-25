""" Generate an infinite sequence of evenly spaced values

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2019-12-11
:Copyright: 2019, Karr Lab
:License: MIT
"""

from decimal import Decimal, getcontext
import collections.abc

from wc_utils.config.core import get_config
UNIFORM_SEQ_PRECISION = get_config()['wc_utils']['misc']['uniform_seq_precision']


class UniformSequence(collections.abc.Iterator):
    """ Generate an infinite sequence of evenly spaced values, especially for non-integral step sizes

    Avoids floating-point roundoff errors by using :obj:`Decimal`\ s to represent the start and step size.
    The `start` and `step` arguments must be integers, floats or strings that can be represented as a
    Decimal with a mantissa that contains no more than `UNIFORM_SEQ_PRECISION` digits.

    Attributes:
        _start (:obj:`Decimal`): starting point of the sequence
        _step (:obj:`Decimal`): step size for the sequence
        _num_steps (:obj:`int`): number of steps taken in the sequence
    """

    def __init__(self, start, step):
        """ Initialize a :obj:`UniformSequence`

        Args:
            start (:obj:`str`, :obj:`int`, or :obj:`float`): starting point of the sequence
            step (:obj:`str`, :obj:`int`, or :obj:`float`): step size for the sequence

        Raises:
            :obj:`ValueError`: if `step` is 0, NaN, or infinite, or
                if the precision in `start` or `step` exceeds `UNIFORM_SEQ_PRECISION`
        """
        self._start = Decimal(start)
        self._step = Decimal(step)
        if not self._step.is_normal():
            raise ValueError(f"UniformSequence: step={step} can't be 0, NaN, infinite, or subnormal")

        # start and step cannot contain more digits than the Decimal precision
        if UNIFORM_SEQ_PRECISION < len(self._start.as_tuple().digits):
            raise ValueError(f"UniformSequence: precision in start={start} exceeds UNIFORM_SEQ_PRECISION "
                             f"threshold={UNIFORM_SEQ_PRECISION}; provide value as a string to avoid roundoff error")
        if UNIFORM_SEQ_PRECISION < len(self._step.as_tuple().digits):
            raise ValueError(f"UniformSequence: precision in step={step} exceeds UNIFORM_SEQ_PRECISION "
                             f"threshold={UNIFORM_SEQ_PRECISION}; provide value as a string to avoid roundoff error")
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
            :obj:`Decimal`: next value in this :obj:`UniformSequence`
        """
        getcontext().prec = UNIFORM_SEQ_PRECISION
        next_value = self._start + self._num_steps * self._step
        self._num_steps += 1
        if next_value.is_zero():
            return 0.
        return next_value

    def next_float(self):
        """ Get next value in the sequence as a float for external use

        Returns:
            :obj:`float`: next value in this :obj:`UniformSequence`
        """
        return float(self.__next__())

    # todo: support scientific notation in truncate() so that sequences like this work
    # ((0, 1E-11), (0, .1E-10, .2E-10, .3E-10, .4E-10, .5E-10, .6E-10, .7E-10, .8E-10, .9E-10)),
    @staticmethod
    def truncate(value):
        """ Truncate a uniform sequence value into fixed-point notation for output

        Raise an exception if truncation loses precision.

        Args:
            value (:obj:`float`): value to truncate to a certain precision

        Returns:
            :obj:`str`: string representation of a uniform sequence value truncated to the maximum
                precision supported

        Raises:
            :obj:`StopIteration`: if the truncated value does not equal `value`
        """
        truncated_value = f'{value:.{UNIFORM_SEQ_PRECISION}f}'
        if Decimal(truncated_value) != Decimal(str(value)):
            raise StopIteration(f'UniformSequence: truncation error:\n'
                                f'value: {value}; truncated_value: {truncated_value} '
                                f'num digits precision: {UNIFORM_SEQ_PRECISION}; ')
        return truncated_value
