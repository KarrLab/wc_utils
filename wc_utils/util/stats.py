""" Statistical utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@mssm.edu>
:Date: 2017-05-26
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import numpy
from math import isclose


class ExponentialMovingAverage(object):
    """ An exponential moving average.

    Each moving average S is computed recursively from the sample values Y:
        S_1 = Y_1
        S_t = alpha * Y_t + (1 - alpha) * S_(t-1)

    Attributes:
        value (:obj:`float`): the current average
        alpha (:obj:`float`): the decay factor        
    """

    def __init__(self, value, alpha=None, center_of_mass=None):
        """ Initialize an ExponentialMovingAverage.

        Args:
            value (:obj:`float`): initial average value
            alpha (:obj:`float`): the decay factor [0, 1]
            center_of_mass (:obj:`float`): a center of mass for initializing alpha, the decay factor
                in an exponential moving average. :obj:`alpha` =  1 / (1 + :obj:`center_of_mass`)

        Raises:
            :obj:`ValueError`: if alpha < 0 or 1 < alpha
        """
        if alpha != None and center_of_mass != None:
            raise ValueError("Only one of `alpha` or `center_of_mass` should be provided")
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
        """ Add a sample to this :obj:`ExponentialMovingAverage`, and update the average.

        Args:
            new_value (:obj:`float`): the next value to contribute to the exponential moving average

        Returns:
            :obj:`float`: the updated exponential moving average
        """
        self.value = (self.alpha * new_value) + (1. - self.alpha) * self.value
        return self.value

    def get_ema(self):
        """ Get the curent average

        Returns:
            :obj:`float`: curent exponential moving average
        """
        return self.value

    def __eq__(self, other):
        """ Compare two exponential moving averages

        Args:
            other (:obj:`ExponentialMovingAverage`): other exponential moving average

        Returns:
            :obj:`bool`: true if exponential moving averages are equal
        """
        if other.__class__ is not self.__class__:
            return False

        return isclose(self.value, other.value) and isclose(self.alpha, other.alpha)

    def __ne__(self, other):
        """ Compare two exponential moving averages

        Args:
            other (:obj:`ExponentialMovingAverage`): other exponential moving average

        Returns:
            :obj:`bool`: true if exponential moving averages are unequal
        """
        return not self.__eq__(other)


def weighted_mean(values, weights, ignore_nan=True):
    """ Calculate weighted mean of a list of values, weighted by :obj:`weights`

    Args:
        values (:obj:`list` of :obj:`float`): values
        weights (:obj:`list` of :obj:`float`): weights
        ignore_nan (:obj:`bool`, optional): if :obj:`True`, ignore `nan` values

    Returns:
        :obj:`float`: mean of :obj:`values`, weighted by :obj:`weights`
    """
    if not ignore_nan and (any(numpy.isnan(values)) or any(numpy.isnan(weights))):
        return numpy.nan

    values = 1. * numpy.array(values)
    weights = 1. * numpy.array(weights)

    tfs = numpy.logical_and(numpy.logical_not(numpy.isnan(values)), weights > 0)
    values = numpy.extract(tfs, values)
    weights = numpy.extract(tfs, weights)
    if values.size == 0:
        return numpy.nan

    return numpy.average(values, weights=weights)


def weighted_percentile(values, weights, percentile, ignore_nan=True):
    """ Calculate percentile of a list of values, weighted by :obj:`weights`

    Args:
        values (:obj:`list` of :obj:`float`): values
        weights (:obj:`list` of :obj:`float`): weights
        percentile (:obj:`float`): percentile
        ignore_nan (:obj:`bool`, optional): if :obj:`True`, ignore `nan` values

    Returns:
        :obj:`float`: weighted percentile of :obj:`values`
    """
    if not ignore_nan and (any(numpy.isnan(values)) or any(numpy.isnan(weights))):
        return numpy.nan

    values = 1. * numpy.array(values)
    weights = 1. * numpy.array(weights)

    tfs = numpy.logical_and(numpy.logical_not(numpy.isnan(values)), weights > 0)
    values = numpy.extract(tfs, values)
    weights = numpy.extract(tfs, weights)
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


def weighted_median(values, weights, ignore_nan=True):
    """ Calculate the median of a list of values, weighted by :obj:`weights`

    Args:
        values (:obj:`list` of :obj:`float`): values
        weights (:obj:`list` of :obj:`float`): weights
        ignore_nan (:obj:`bool`, optional): if :obj:`True`, ignore `nan` values

    Returns:
        :obj:`float`: weighted median of :obj:`values`
    """
    if not ignore_nan and (any(numpy.isnan(values)) or any(numpy.isnan(weights))):
        return numpy.nan

    values = 1. * numpy.array(values)
    weights = 1. * numpy.array(weights)

    tfs = numpy.logical_and(numpy.logical_not(numpy.isnan(values)), weights > 0)
    values = numpy.extract(tfs, values)
    weights = numpy.extract(tfs, weights)
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


def weighted_mode(values, weights, ignore_nan=True):
    """ Calculate the mode of a list of values, weighted by :obj:`weights`

    Args:
        values (:obj:`list` of :obj:`float`): values
        weights (:obj:`list` of :obj:`float`): weights
        ignore_nan (:obj:`bool`, optional): if :obj:`True`, ignore `nan` values

    Returns:
        :obj:`float`: weighted mode of :obj:`values`
    """
    if not ignore_nan and (any(numpy.isnan(values)) or any(numpy.isnan(weights))):
        return numpy.nan

    values = 1. * numpy.array(values)
    weights = 1. * numpy.array(weights)

    tfs = numpy.logical_and(numpy.logical_not(numpy.isnan(values)), weights > 0)
    values = numpy.extract(tfs, values)
    weights = numpy.extract(tfs, weights)
    if values.size == 0:
        return numpy.nan

    ind = numpy.argsort(values)
    sorted_values = values[ind]
    sorted_weights = weights[ind]

    cum_weights = sorted_weights.cumsum()

    tfs = numpy.concatenate(((numpy.diff(sorted_values[::-1])[::-1] < 0), [True]))

    sorted_values = numpy.extract(tfs, sorted_values)
    cum_weights = numpy.extract(tfs, cum_weights)

    sorted_weights = numpy.diff(numpy.concatenate(([0], cum_weights)))
    return sorted_values[numpy.argmax(sorted_weights)]
