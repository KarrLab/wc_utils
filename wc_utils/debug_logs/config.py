import yaml
import sys
""" Configure debug log files.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-22
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from os import makedirs, path
from pkg_resources import resource_filename
from wc_utils.config.core import ConfigPaths
try:
    # try importing logging2 because logging2 can be installed in Windows
    # although logging2 relies on syslog which only works on Unix
    import logging2
except ModuleNotFoundError:  # pragma: no cover
    logging2 = None

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
            :obj:`dict`: handlers 
            :obj:`dict`: loggers

        Args:
            config_path (:obj:`str`): path to configuration file written in YAML
        """

        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=yaml.SafeLoader)

        return LoggerConfigurator.from_dict(config)

    @staticmethod
    def from_dict(config):
        """ Create and configure logs from a dictionary which describes their configuration

        Args:
            config (:obj:`dict`): dictionary of logger configurations

        Returns:
            :obj:`dict`: handlers 
            :obj:`dict`: loggers

        Raises:
            :obj:`log.ConfigurationError`: For unsupported handler types
            :obj:`ModuleNotFoundError`: If `logging2` is not installed
        """
        if logging2 is None:
            raise ModuleNotFoundError("'logging2' must be installed")  # pragma: no cover

        # create handlers
        # risky: handlers are shared between loggers. thus,
        # any modifications of handlers by one logger may affect another.
        handlers = {}
        for name, config_handler in config.get('handlers', {}).items():
            extra_opts = set(config_handler.keys()).difference(set(['class', 'filename', 'encoding', 'level']))
            if extra_opts:
                raise ConfigurationError('Handler configuration does not support options "{}"'.format(
                    '", "'.join(extra_opts)))

            class_name = config_handler.get('class', 'StdOutHandler')
            level = getattr(logging2.LogLevel, config_handler.get('level', 'debug').lower())

            if class_name in ['StdErrHandler', 'StdOutHandler']:
                cls = getattr(logging2, class_name)
                handler = cls(name=name, level=level)

            elif class_name == 'FileHandler':
                filename = path.expanduser(config_handler['filename'])

                if not path.isdir(path.dirname(filename)):
                    makedirs(path.dirname(filename))

                if not path.isfile(filename):
                    open(filename, 'w').close()

                encoding = config_handler.get('encoding', 'utf-8')

                handler = logging2.FileHandler(filename, name=name, level=level, encoding=encoding)

            else:
                raise ConfigurationError('Unsupported handler class: ' + class_name)

            handlers[name] = handler

        # create loggers
        loggers = {}
        for name, config_logger in config.get('loggers', {}).items():
            extra_opts = set(config_logger.keys()).difference(set(['template', 'timezone', 'handler', 'additional_context']))
            if extra_opts:
                raise ConfigurationError('Logger configuration does not support options "{}"'.format(
                    '", "'.join(extra_opts)))

            template = config_logger.get('template', None)
            timezone = config_logger.get('timezone', None)
            additional_context = config_logger.get('additional_context', None)

            if 'handler' in config_logger and config_logger['handler'] in handlers:
                handler = handlers[config_logger['handler']]
            else:
                raise ConfigurationError("A handler must be defined.")

            loggers[name] = logging2.Logger(name=name, template=template, timezone=timezone,
                                            handler=handler, additional_context=additional_context)

        # return handlers and loggers
        return handlers, loggers


class ConfigurationError(Exception):
    """ An error in a logging configuration """
    pass
