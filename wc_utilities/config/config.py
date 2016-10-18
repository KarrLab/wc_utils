"""
Main configuration module.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utilities.debug_logs.config_from_files_and_env import ConfigFromFilesAndEnv
from wc_utilities.debug_logs.debug import MakeLoggers

class ConfigAll(object):
    """Manage global registry of loggers.
    
    Support sharing of loggers among multiple modules that use the same config_data.

    Attributes:
        loggers_registry (:obj:`dict`): a registry of all loggers
    """

    loggers_registry={}
    
    @staticmethod
    def setup_logger( config_data ):
        """Setup and return a list of loggers.
        
        If the loggers specified by config_data have already been setup, return them.
        Otherwise, create these logger(s), save a dict of references to them in 
        in the loggers registry, and return the dict.
        
        Args:
            config_data (:obj:`dict`): nested dictionaries containing configuration data

        Returns:
            :obj:`dict`: a dict of log.loggers instances
        """
        key = str(config_data)
        # TODO: address the issue that arises when multiple config files point to the same log files
        if key in ConfigAll.loggers_registry:
            return( ConfigAll.loggers_registry[key] )

        log_config = ConfigFromFilesAndEnv.setup( config_data )
        new_loggers = MakeLoggers().setup_logger( log_config )
        ConfigAll.loggers_registry[ key ] = new_loggers
        return new_loggers
