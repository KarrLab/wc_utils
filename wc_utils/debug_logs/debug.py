""" Debugging/info log

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-21
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
import sys

import log
from . import config_log
from wc_utils.debug_logs.config_log import ConfigLog
from wc_utils.debug_logs.config_from_files_and_env import ConfigFromFilesAndEnv

class MakeLoggers(object):
    ''' Manage debug loggers

    Create and store debug loggers.

    Attributes:
        loggers (:obj:`list`): list of loggers stored by a MakeLoggers instance
    '''

    def __init__(self):
        self.loggers = None
        
    def setup_logger(self, options):
        """ Configure and create a log from a log description in a nested dict.
        
        Typically the log description is obtained by reading a .cfg file with ConfigObj.
        TODO: document required structure of options

        Args:
            options (:obj:`dict`): a configuration

        Returns:
            :obj:`type`: a list of loggers created
        """

        if 'log' in options and 'debug' in options['log']:
            options = deepcopy(options['log']['debug'])
        for name, handler in options['handlers'].items():
            if handler['class'] == 'FileHandler':
                for key in handler:
                    if key not in ['class', 'filename', 'mode', 'encoding', 'errors', 'buffering']:
                        handler.pop(key)

            elif handler['class'] == 'StreamHandler':
                for key in handler:
                    if key not in ['class', 'stream']:
                        handler.pop(key)

        _, _, loggers = ConfigLog.from_dict(options)
        self.loggers = loggers
        return self


    def get_logger(self, name, loggers=None):
        """ Returns logger with name `name`. Optionally, search for logger in dict `loggers`.

        Args:
            name (:obj:`str`): log name
            loggers (:obj:`dict`, optional): dictionary of loggers to search
        """

        if loggers is None:
            loggers = self.loggers
            if loggers is None:
                raise ValueError( "No logger initialized." )

        if name not in loggers:
            raise ValueError( "logger named '{}' not found.".format(name) )
            
        return loggers[name]
