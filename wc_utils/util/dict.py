""" dict utils

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-25
:Copyright: 2016, Karr Lab
:License: MIT
"""

from six import iteritems

class DictUtil(object):
    """ Dictionary utility methods """

    @staticmethod
    def nested_in(dict, keys, key_delimiter='.'):
        """ Determines in the nested key sequence `keys` is in the dictionary `dict`

        Args:
            dict (:obj:`dict`): dictionary to retrieve value from
            keys (:obj:`str` or :obj:`list`): list of nested keys to retrieve
            key_delimiter (:obj:`str`, optional): delimiter for `keys`

        Returns:
            :obj:`bool`: Whether or not the nested key sequence `keys` is in the dictionary `dict`
        """

        if isinstance(keys, str):
            keys = keys.split(key_delimiter)

        nested_dict = dict
        for key in keys:
            if key not in nested_dict:
                return False
            nested_dict = nested_dict[key]

        return True

    @staticmethod
    def nested_get(dict, keys, key_delimiter='.'):
        """ Get the value of a nested dictionary at the nested key sequence `keys`

        Args:
            dict (:obj:`dict`): dictionary to retrieve value from
            keys (:obj:`str` or :obj:`list`): list of nested keys to retrieve
            key_delimiter (:obj:`str`, optional): delimiter for `keys`

        Returns:
            :obj:`object`: The value of `dict` from the nested keys list
        """

        if isinstance(keys, str):
            keys = keys.split(key_delimiter)

        nested_dict = dict
        for key in keys:
            nested_dict = nested_dict[key]

        return nested_dict

    @staticmethod
    def nested_set(dict, keys, value, key_delimiter='.'):
        """ Set the value of a nested dictionary at the nested key sequence `keys`

        Args:
            dict (:obj:`dict`): dictionary to retrieve value from
            keys (:obj:`str` or :obj:`list`): list of nested keys to retrieve
            value (:obj:`object`): desired value of `dict` at key sequence `keys`
            key_delimiter (:obj:`str`, optional): delimiter for `keys`

        Returns:
            :obj:`object`: Modified input dictionary
        """

        if isinstance(keys, str):
            keys = keys.split(key_delimiter)

        last_key = keys.pop()

        nested_dict = dict
        for key in keys:
            if key not in nested_dict:
                nested_dict[key] = {}
            nested_dict = nested_dict[key]

        nested_dict[last_key] = value

        return dict

    @staticmethod
    def to_string_sorted_by_key(d):
        '''Provide a string representation of a dictionary sorted by key.

        Args:
            d (:obj:`dict`): dictionary

        Returns:
            :obj:`str`: string representation of a dictionary sorted by key
        '''
        if d is None:
            return '{}'
        else:
            return '{' + ', '.join('{!r}: {!r}'.format(key, d[key]) for key in sorted(d)) + '}'

    @staticmethod
    def filtered_dict(d, filter_keys):
        '''Create a new dict from `d`, with keys filtered by `filter_keys`.

        Returns:
            dict: a new dict containing the entries in `d` whose keys are in `filter_keys`.
        '''
        return {k:v for (k,v) in iteritems(d) if k in filter_keys}

    @staticmethod
    def filtered_iteritems(d, filter_keys):
        '''A generator that filters a dict's iteritems to keys in `filter_keys`.

        Yields:
            tuple: (key, value) tuples from `d` whose keys are in `filter_keys`.
        '''
        for key, val in iteritems(d):
            if key not in filter_keys:
                continue
            yield key, val
