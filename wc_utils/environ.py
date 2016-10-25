""" Environment utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-24
:Copyright: 2016, Karr Lab
:License: MIT
"""


import contextlib
import os


class EnvironUtils(object):

    @staticmethod
    @contextlib.contextmanager    
    def make_temp_environ(**environ):
        """ Temporarily set environment variables.:

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
