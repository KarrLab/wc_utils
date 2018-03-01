""" Configure debug log files.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-22
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from copy import deepcopy
from log.errors import ConfigurationError
from log.formatters import Formatter
from log.handlers import FileHandler, StreamHandler
from log.levels import LogLevel
from log.loggers import Logger
from os import makedirs, path
from pkg_resources import resource_filename
from wc_utils.config.core import ConfigPaths
import sys
import yaml
import copy

paths = ConfigPaths(
    default=resource_filename('wc_utils', 'debug_logs/config.default.cfg'),
    schema=resource_filename('wc_utils', 'debug_logs/config.schema.cfg'),
    user=(
        'debug.cfg',
        path.expanduser('~/.wc/debug.cfg'),
    ),
)


class LoggerConfigurator(object):
    ''' A class with static methods that configures log files. '''

    @staticmethod
    def from_yaml(config_path):
        """ Create and configure logs from a YAML file which describes their configuration

        Deprecated in favor of ConfigObj

        Returns:
            :obj:`tuple`: tuple of created formatters, handlers, loggers

        Args:
            config_path (:obj:`str`): path to configuration file written in YAML
        """

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        return LoggerConfigurator.from_dict(config)

    @staticmethod
    def from_dict(config):
        """ Create and configure logs from a dictionary which describes their configuration

        Args:
            config (:obj:`dict`): dictionary of logger configurations

        Returns:
            :obj:`tuple`: tuple created formatters, handlers, loggers

        Raises:
            :obj:`log.ConfigurationError`: For unsupported handler types or undefined formatters
        """

        config = deepcopy(config)

        # create formatters
        formatters = {}
        if 'formatters' in config:
            for name, config_formatter in config['formatters'].items():
                formatters[name] = Formatter(name=name, **config_formatter)

        # create handlers
        # risky: handlers are shared between loggers. thus,
        # any modifications of handlers by one logger may affect another.
        handlers = {}
        if 'handlers' in config:
            for name, config_handler in config['handlers'].items():
                class_name = config_handler.pop('class')

                if class_name == 'StreamHandler':
                    stream = getattr(sys, config_handler.pop('stream'))
                    handler = StreamHandler(stream, name=name, **config_handler)

                elif class_name == 'FileHandler':
                    filename = path.expanduser(config_handler.pop('filename'))

                    if not path.isdir(path.dirname(filename)):
                        makedirs(path.dirname(filename))

                    if not path.isfile(filename):
                        open(filename, 'w').close()

                    handler = FileHandler(filename, name=name, **config_handler)

                else:
                    raise ConfigurationError('Unsupported handler class: ' + class_name)

                handlers[name] = handler

        # create loggers
        loggers = {}
        if 'loggers' in config:
            for name, config_logger in config['loggers'].items():
                if 'level' in config_logger:
                    level = getattr(LogLevel, config_logger.pop('level'))
                else:
                    raise ConfigurationError("Level must be defined")

                if 'formatters' in config_logger and config_logger['formatters']:
                    try:
                        logger_formatters = [formatters[formatter_name]
                                             for formatter_name in config_logger.pop('formatters')]
                    except KeyError as e:
                        raise ConfigurationError("Formatter {} not found.".format(e))
                else:
                    raise ConfigurationError("At least one formatter must be defined.")

                if 'handlers' in config_logger and config_logger['handlers']:
                    logger_handlers = [handlers[handler_name] for handler_name in config_logger.pop('handlers')]
                else:
                    raise ConfigurationError("At least one handler must be defined.")

                # copying the formatter avoids unexpected formats caused by changes to shared formatters
                loggers[name] = Logger(name=name, level=level,
                                       formatters=copy.deepcopy(logger_formatters),
                                       handlers=logger_handlers, **config_logger)

        return formatters, handlers, loggers
