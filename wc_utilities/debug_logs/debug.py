""" Debugging/info log

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-21
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from wc.config.core import config
import log.config
import sys


def setup(options=None):
    """ Create and configure logs

    Args:
        options (:obj:`dict`): dictionary of configurations
    """

    if not options:
        options = deepcopy(config['log']['debug'])
        for name, handler in options['handlers'].items():
            if handler['class'] == 'FileHandler':
                for key in handler:
                    if key not in ['class', 'filename', 'mode', 'encoding', 'errors', 'buffering']:
                        handler.pop(key)

            elif handler['class'] == 'StreamHandler':
                for key in handler:
                    if key not in ['class', 'stream']:
                        handler.pop(key)

    _, _, loggers = log.config.Config.from_dict(options)
    return loggers


def get_logger(name, loggers=None):
    """ Returns logger with name `name`. Optionally, search for logger in 
    passed in dictionary.

    Args:
        name (:obj:`str`): log name
        loggers (:obj:`dict`, optional): dictionary of loggers to search over
    """

    if loggers is None:
        module = sys.modules[__name__]
        loggers = getattr(module, 'loggers')

    return loggers[name]


# setup logs from configuration files
loggers = setup()
# :obj:`dict`: list of available loggers
