""" Generate an infinite sequence of evenly spaced values

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2019-12-11
:Copyright: 2019, Karr Lab
:License: MIT
"""

from fractions import Fraction
import collections

from wc_utils.config.core import get_config
uniform_seq_precision = get_config()['wc_utils']['misc']['uniform_seq_precision']


class UniformSequence(collections.abc.Iterator):
    """ Generate an infinite sequence of evenly spaced values, especially for non-integral step sizes

    Avoids floating-point roundoff errors by using a :obj:`Fraction` to represent the step size as
    a ratio of integers, and raising exceptions when errors occur.

    Attributes:
        _start (:obj:`float`): starting point of the sequence
        _fraction_step (:obj:`Fraction`): step size for the sequence
        _num_steps (:obj:`int`): number of steps taken in the sequence
    """
    MAX_DENOMINATOR = 1_000_000

    def __init__(self, start, step):
        """ Initialize a :obj:`UniformSequence`

        Args:
            start (:obj:`float`): starting point of the sequence
            step (:obj:`float`): step size for the sequence
        """
        self._start = start
        self._fraction_step = Fraction(step).limit_denominator(max_denominator=self.MAX_DENOMINATOR)
        if step * self._fraction_step.denominator != self._fraction_step.numerator:
            raise ValueError(f"UniformSequence: step {step} can't be a fraction of integers "
                             f"denominator <= {self.MAX_DENOMINATOR}")
        self._num_steps = 0

    def __iter__(self):
        return self

    def __next__(self):
        """ Get next value in the sequence

        Raises:
            :obj:`StopIteration`: if the next value encounters a floating-point rounding error
        """
        next_value = self._start + \
            (self._num_steps * self._fraction_step.numerator) / self._fraction_step.denominator
        if (next_value - self._start) * self._fraction_step.denominator != \
            self._num_steps * self._fraction_step.numerator:
            raise StopIteration(f'UniformSequence: floating-point rounding error:\n'
                                f'_start: {self._start}; '
                                f'_num_steps: {self._num_steps}; '
                                f'_fraction_step.numerator: {self._fraction_step.numerator}; '
                                f'_fraction_step.denominator: {self._fraction_step.denominator}')
        # ensure that next_value can be safely truncated
        self.truncate(next_value)
        self._num_steps += 1
        return next_value

    @staticmethod
    def truncate(value):
        """ Truncate a uniform sequence value into fixed-point notation for output

        Raise an exception if truncation loses precision.

        Raises:
            :obj:`StopIteration`: if the truncated value does not equal `value`
        """
        truncated_value = f'{value:.{uniform_seq_precision}f}'
        if float(truncated_value) != value:
            raise StopIteration(f'UniformSequence: truncation error:\n'
                                f'value: {value}; truncated_value: {truncated_value} '
                                f'num digits precision: {uniform_seq_precision}; ')
        return truncated_value
