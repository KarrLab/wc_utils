from log.errors import ConfigurationError
from log.formatters import Formatter
from log.handlers import FileHandler, StreamHandler
from log.levels import LogLevel
from log.loggers import Logger
from os import makedirs, path
import sys
import yaml


class ConfigLog(object):

    @staticmethod
    def from_yaml(config_path):
        """ Create and configure logs from a YAML file which describes their configuration

        Returns:
            :obj:`tuple`: tuple created formatters, handlers, loggers

        Args:
            config_path (:obj:`str`): path to configuration file in YAML format
        """

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        return Config.from_dict(config)

    @staticmethod
    def from_dict(config):
        """ Create and configure logs from a dictionary which describes their configuration

        Args:
            config (:obj:`dict`): dictionary of logger configurations

        Returns:
            :obj:`tuple`: tuple created formatters, handlers, loggers

        Raises:
            :obj:`log.ConfigurationError`: For unsupported handler types
        """

        # create formatters
        formatters = {}
        if 'formatters' in config:
            for name, config_formatter in config['formatters'].items():
                formatters[name] = Formatter(name=name, **config_formatter)

        # create handlers
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
                    level = None

                if 'formatters' in config_logger:
                    logger_formatters = [formatters[formatter_name]
                                         for formatter_name in config_logger.pop('formatters')]
                else:
                    logger_formatters = None

                if 'handlers' in config_logger:
                    logger_handlers = [handlers[handler_name] for handler_name in config_logger.pop('handlers')]
                else:
                    logger_handlers = None

                print("\ncreating logger {} with config:".format( name ))
                print( kws( name=name, level=level, template=logger_formatters[0].template,
                    formatters=logger_formatters, handlers=logger_handlers, **config_logger ))
                loggers[name] = Logger(name=name, level=level, template=logger_formatters[0].template,
                    formatters=logger_formatters, handlers=logger_handlers, **config_logger)

        return formatters, handlers, loggers

def kws(**kwargs):
    if kwargs is not None:
        for key, value in kwargs.items():
            print( "%s == %s" %(key,value) )