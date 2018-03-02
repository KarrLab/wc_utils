""" dict utils

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-08-25
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""


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
        """Provide a string representation of a dictionary sorted by key.

        Args:
            d (:obj:`dict`): dictionary

        Returns:
            :obj:`str`: string representation of a dictionary sorted by key
        """
        if d is None:
            return '{}'
        else:
            return '{' + ', '.join('{!r}: {!r}'.format(key, d[key]) for key in sorted(d)) + '}'

    @staticmethod
    def filtered_dict(d, filter_keys):
        """Create a new dict from `d`, with keys filtered by `filter_keys`.

        Args:
            d (:obj:`dict`): dictionary to filter.
            filter_keys (:obj:`list` of :obj:`str`): list of keys to retain.

        Returns:
            :obj:`dict`: a new dict containing the entries in `d` whose keys are in `filter_keys`.
        """
        return {k: v for (k, v) in d.items() if k in filter_keys}

    @staticmethod
    def filtered_iteritems(d, filter_keys):
        """A generator that filters a dict's items to keys in `filter_keys`.

        Args:
            d (:obj:`dict`): dictionary to filter.
            filter_keys (:obj:`list` of :obj:`str`): list of keys to retain.

        Yields:
            :obj:`tuple`: (key, value) tuples from `d` whose keys are in `filter_keys`.
        """
        for key, val in d.items():
            if key not in filter_keys:
                continue
            yield key, val

    @staticmethod
    def set_value(d, target_key, new_value, match_type=True):
        """ Set values of target keys in a nested dictionary

        Consider every `key`-`value` pair in nested dictionary `d`. If `value` is not a `dict`,
        and `key` is equal to `target_key` then replace `value` with `new_value`. However, if
        `match_type` is set, only replace `value` if it is an instance of `new_value`'s type.
        Caution: `set_value()` will loop infinitely on self-referential dicts.

        Args:
            d (:obj:`dict`): dictionary to modify
            target_key (:obj:`obj`): key to match
            new_value (:obj:`obj`): replacement value
            match_type (:obj:`bool`, optional): if set, only replace values that are instances
                of the type of `new_value`
        """
        for key,val in d.items():
            if isinstance(val, dict):
                DictUtil.set_value(val, target_key, new_value, match_type=match_type)
            elif key == target_key and (not match_type or isinstance(val, type(new_value))):
                d[target_key] = new_value
