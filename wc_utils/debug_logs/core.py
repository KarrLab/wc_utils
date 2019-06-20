""" Debugging/info log

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-25
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from copy import deepcopy
import sys

from wc_utils.debug_logs.config import LoggerConfigurator


class DebugLogsManager(object):
    ''' Manage debug logs

    Create and store debug logs.

    Attributes:
        logs (:obj:`dict`): dictionary of logs stored by a DebugLogsManager instance
    '''

    def __init__(self):
        self.logs = None

    def setup_logs(self, options):
        """ Configure and create a log from a log description in a nested dict.

        Typically the log description is obtained by reading a .cfg file with ConfigObj.

        Args:
            options (:obj:`dict`): a configuration

        Returns:
            :obj:`DebugLogsManager`: this `DebugLogsManager`
        """

        if 'debug_logs' in options:
            options = options['debug_logs']

        _, loggers = LoggerConfigurator.from_dict(options)
        self.logs = loggers
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
            raise ValueError("log named '{}' not found in logs '{}'.".format(name,
                                                                             list(logs.keys())))

        return logs[name]

    def __str__(self):
        """ Return string representation of this `DebugLogsManager`'s logs

        Returns:
            :obj:`str`: the name, level, template and filename (if used) for each log
        """

        def logger_desc(log):
            rv = []
            for attr in ['template']:
                rv.append("{}: {}".format(attr, getattr(log, attr)))
            for handler in log.handlers:
                try:
                    filename = handler.fh.name
                    rv.append("{}: {}".format('filename', filename))
                except:
                    rv.append("no filename associated with handler")
            return '\n\t'.join(rv)
        if self.logs is None or not len(self.logs):
            return 'No logs configured'
        log_descriptions = ['logs:']
        for name, log in self.logs.items():
            log_descriptions.append("{}:\n\t{}".format(name, logger_desc(log)))
        return '\n'.join(log_descriptions)
