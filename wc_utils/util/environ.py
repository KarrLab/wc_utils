""" Environment utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-24
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""


import contextlib
import os


class EnvironUtils(object):

    @staticmethod
    @contextlib.contextmanager
    def make_temp_environ(**environ):
        """ Temporarily set environment variables:

            with make_temp_environ(PLUGINS_DIR=u'test/plugins'):
                "PLUGINS_DIR" in os.environ
                    True
                "PLUGINS_DIR" in os.environ
                    False

        Args:
            environ (:obj:`dict`): dictionary of desired environment variable values

        From http://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment
        """

        old_environ = dict(os.environ)
        os.environ.update(environ)
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(old_environ)


class MakeEnvironArgs(object):

    CONFIG = 'CONFIG'
    DOT = '__DOT__'
    def __init__(self):
        self.env = {}

    def add_to_env(self, path, value):
        """ Add a value to an environment dict

        Args:
            path (:obj:`list` of :obj:`str`): configuration path components
            value (:obj:`obj`): the value that the path should have

        Returns:
            :obj:`dict`: the updated environment
        """
        name = [MakeEnvironArgs.CONFIG]
        for element in path:
            name.append(MakeEnvironArgs.DOT)
            name.append(element)
        self.env[''.join(name)] = value
        return self.env

    def get_env(self):
        return self.env
