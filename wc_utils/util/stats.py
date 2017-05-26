""" Statistical utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@mssm.edu>
:Date: 2017-05-26
:Copyright: 2016-2017, Karr Lab
:License: MIT
"""

import numpy


class ExponentialMovingAverage(object):
    """An exponential moving average.

    Each moving average S is computed recursively from the sample values Y:
        S_1 = Y_1
        S_t = alpha * Y_t + (1 - alpha) * S_(t-1)

    Attributes:
        value (:obj:`float`): the current average
        alpha (:obj:`float`): the decay factor        
    """

    def __init__(self, value, alpha=None, center_of_mass=None):
        """Initialize an ExponentialMovingAverage.

        Args:
            value (:obj:`float`): initial average value
            alpha (:obj:`float`): the decay factor [0, 1]
            center_of_mass (:obj:`float`): a center of mass for initializing alpha, the decay factor
                in an exponential moving average. :obj:`alpha` =  1 / (1 + :obj:`center_of_mass`)

        Raises:
            :obj:`ValueError`: if alpha < 0 or 1 < alpha
        """
        if alpha != None:
            self.alpha = float(alpha)
        elif center_of_mass != None:
            self.alpha = 1. / (1. + center_of_mass)
        else:
            raise ValueError("`alpha` or `center_of_mass` must be provided")
        if self.alpha < 0 or 1 < self.alpha:
            raise ValueError("`alpha` must satisfy 0 <= `alpha` <= 1: but `alpha`={}".format(self.alpha))
        self.value = float(value)

    def add_value(self, new_value):
        """Add a sample to this :obj:`ExponentialMovingAverage`, and update the average.

        Args:
            new_value (:obj:`float`): the next value to contribute to the exponential moving average

        Returns:
            :obj:`float`: the updated exponential moving average
        """
        self.value = (self.alpha * new_value) + (1. - self.alpha) * self.value
        return self.value

    def get_value(self):
        """ Get the curent average

        Returns:
            :obj:`float`: curent exponential moving average
        """
        return self.value


def weighted_percentile(values, weights, percentile):
    """ Calculate percentile of a list of values, weighted by :obj:`weights`

    Args:
        values (:obj:`list` of :obj:`float`): values
        weights (:obj:`list` of :obj:`float`): weights
        percentile (:obj:`float`): percentile

    Returns:
        :obj:`float`: weighted percentile of :obj:`values`
    """
    values = 1. * numpy.array(values)
    weights = 1. * numpy.array(weights)

    values = numpy.extract(weights > 0, values)
    weights = numpy.extract(weights > 0, weights)
    if values.size == 0:
        return numpy.nan

    ind = numpy.argsort(values)
    sorted_values = values[ind]
    sorted_weights = weights[ind]
    total_weight = sorted_weights.sum()

    probabilities = sorted_weights.cumsum() / total_weight

    ind = numpy.searchsorted(probabilities, percentile / 100.)
    if probabilities[ind] == percentile / 100.:
        return numpy.mean(sorted_values[ind:ind+2])
    else:
        return sorted_values[ind]


def weighted_median(values, weights):
    """ Calculate the median of a list of values, weighted by :obj:`weights`

    Args:
        values (:obj:`list` of :obj:`float`): values
        weights (:obj:`list` of :obj:`float`): weights

    Returns:
        :obj:`float`: weighted median of :obj:`values`
    """
    values = 1. * numpy.array(values)
    weights = 1. * numpy.array(weights)

    values = numpy.extract(weights > 0, values)
    weights = numpy.extract(weights > 0, weights)
    if values.size == 0:
        return numpy.nan

    ind = numpy.argsort(values)
    sorted_values = values[ind]
    sorted_weights = weights[ind]
    total_weight = sorted_weights.sum()

    probabilities = sorted_weights.cumsum() / total_weight

    ind = numpy.searchsorted(probabilities, 0.5)
    if probabilities[ind] == 0.5:
        return numpy.mean(sorted_values[ind:ind+2])
    else:
        return sorted_values[ind]
