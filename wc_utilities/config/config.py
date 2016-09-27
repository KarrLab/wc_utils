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

    loggers_registry={}
    
    @staticmethod
    def setup_logger( config_data ):
        """Setup and return a list of loggers.
        
        If the list of loggers has already been setup, simply return
        it from the loggers registry. Otherwise, set it up, save it
        in the registry, and return a pointer to it.
        This enables sharing of loggers among multiple modules that use
        the same config_data.
        """
        key = str(config_data)
        # TODO: address the issue that arises when multiple config files point to the same log files
        if key in ConfigAll.loggers_registry:
            return( ConfigAll.loggers_registry[key] )

        log_config = ConfigFromFilesAndEnv.setup( config_data )
        new_loggers = MakeLoggers().setup_logger( log_config )
        ConfigAll.loggers_registry[ key ] = new_loggers
        return new_loggers
