""" Environment utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-24
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import contextlib
import os


class EnvironUtils(object):
    """ A context manager that temporarily sets environment variables
    """

    @staticmethod
    @contextlib.contextmanager
    def make_temp_environ(**environ):
        """ Temporarily set environment variables:

        # assume 'NO_SUCH_ENV_VAR' is not set in the environment
        assert 'NO_SUCH_ENV_VAR' not in os.environ
        with EnvironUtils.make_temp_environ(NO_SUCH_ENV_VAR='test_value'):
            assert os.environ['NO_SUCH_ENV_VAR'] == 'test_value'
        assert 'NO_SUCH_ENV_VAR' not in os.environ

        When used to modify configuration variables, `ConfigManager().get_config` must be called after the
        temporary environment variables are set by `make_temp_environ()`.

        From http://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment

        Args:
            environ (:obj:`dict`): dictionary mapping environment variable names to desired temporary values
        """
        old_environ = dict(os.environ)
        os.environ.update(environ)
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(old_environ)

    @staticmethod
    @contextlib.contextmanager
    def temp_config_env(path_value_pairs):
        """ Create a temporary environment of configuration values

        Args:
            path_value_pairs (:obj:`list`): iterator over path, value pairs; 'path' is the hierarchical
                path to a config value, and 'value' is its value
        """
        tmp_conf_dict = ConfigEnvDict().prep_tmp_conf(path_value_pairs)
        old_environ = dict(os.environ)
        os.environ.update(tmp_conf_dict)
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(old_environ)


class ConfigEnvDict(object):

    CONFIG = 'CONFIG'
    DOT = '__DOT__'
    def __init__(self):
        self.env = {}

    def add_config_value(self, path, value):
        """ Add a value to a configuration environment dictionary

        Args:
            path (:obj:`list` of :obj:`str`): configuration path components
            value (:obj:`obj`): the value the path should be given

        Returns:
            :obj:`dict`: the updated configuration environment dictionary
        """
        name = [ConfigEnvDict.CONFIG]
        for element in path:
            name.append(ConfigEnvDict.DOT)
            name.append(element)
        self.env[''.join(name)] = value
        return self.get_env_dict()

    def get_env_dict(self):
        """ Get the configuration environment dictionary

        Returns:
            :obj:`dict`: the configuration environment dictionary
        """
        return self.env

    def prep_tmp_conf(self, path_value_pairs):
        """ Create a config environment dictionary

        Args:
            path_value_pairs (:obj:`list`): iterator over path, value pairs; 'path' is the hierarchical
                path to a config value, and 'value' is its value

        Returns:
            :obj:`dict`: a config environment dictionary for the path, value pairs

        Raises:
            :obj:`ValueError`: if a value is not a string
        """
        for path, value in path_value_pairs:
            if not isinstance(value, str):
                raise ValueError(f"environment variable values are strings, but 'value' ({value}) is a(n) {type(value).__name__}")
            self.add_config_value(path, value)
        return self.get_env_dict()
