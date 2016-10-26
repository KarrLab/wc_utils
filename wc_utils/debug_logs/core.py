""" Debugging/info log

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-25
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
import sys

import log
from wc_utils.debug_logs.config import LoggerConfigurator


class DebugLogsManager(object):
    ''' Manage debug logs

    Create and store debug logs.

    Attributes:
        logs (:obj:`list`): list of logs stored by a DebugLogsManager instance
    '''

    def __init__(self):
        self.logs = None

    def setup_logs(self, options):
        """ Configure and create a log from a log description in a nested dict.

        Typically the log description is obtained by reading a .cfg file with ConfigObj.

        Args:
            options (:obj:`dict`): a configuration

        Returns:
            :obj:`type`: a list of logs created
        """

        if 'debug_logs' in options:
            options = deepcopy(options['debug_logs'])
        for name, handler in options['handlers'].items():
            if handler['class'] == 'FileHandler':
                for key in handler:
                    if key not in ['class', 'filename', 'mode', 'encoding', 'errors', 'buffering']:
                        handler.pop(key)

            elif handler['class'] == 'StreamHandler':
                for key in handler:
                    if key not in ['class', 'stream']:
                        handler.pop(key)

        _, _, logs = LoggerConfigurator.from_dict(options)
        self.logs = logs
        return self

    def get_log(self, name, logs=None):
        """ Returns log with name `name`. Optionally, search for log in dict `logs`.

        Args:
            name (:obj:`str`): log name
            logs (:obj:`dict`, optional): dictionary of logs to search
        """

        if logs is None:
            logs = self.logs
            if logs is None:
                raise ValueError("No log initialized.")

        if name not in logs:
            raise ValueError("log named '{}' not found.".format(name))

        return logs[name]