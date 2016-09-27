""" Configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

from configobj import ConfigObj
from configobj import flatten_errors, get_extra_values
from validate import Validator, is_boolean, is_float, is_integer, is_list, is_string, VdtTypeError
from wc_utilities.util.dict import DictUtil
import os
import sys

class ConfigFromFilesAndEnv(object):
    """Obtain configuration information from ini files and/or environment variables.
    
    Also validate the configuration against a configuration schema.
    """

    @staticmethod
    def setup( config_constants ):
        return ConfigFromFilesAndEnv._setup( config_constants.DEFAULT_CONFIG_FILENAME, 
            config_constants.CONFIG_SCHEMA_FILENAME, 
            user_config_filenames=config_constants.USER_CONFIG_FILENAMES)
        
    @staticmethod
    def _setup(DEFAULT_CONFIG_FILENAME, CONFIG_SCHEMA_FILENAME, extra_config=None, 
        user_config_filenames=None):
        """ Setup configuration

        1. Setup configuration from default values specified in `DEFAULT_CONFIG_FILENAME`.
        2. If user_config_filenames is set, find the first file in it that exists, and override the default 
           configuration with the values specified in the file.
        3. Override configuration with values from environment variables. Environment variables
           can be set with the following syntax:
               CONFIG.level1.level2...=val 
        4. Override configuration with additional configuration in `extra_config`.
        5. Validate configuration against the schema specified in `CONFIG_SCHEMA_FILENAME`.
        
        Sets GlobalConfig.config with these configuration settings

        Args:
            extra_config (:obj:`dict`, optional): additional configuration to override

        Raises:
            :obj:`InvalidConfigError`: if configuration doesn't validate against schema
        """

        # read configuration schema/specification
        config_specification = ConfigObj(CONFIG_SCHEMA_FILENAME, list_values=False, _inspec=True)

        # read default configuration
        config = ConfigObj(infile=DEFAULT_CONFIG_FILENAME, configspec=config_specification)

        # read user's configuration files
        if not user_config_filenames is None:
            for user_config_filename in user_config_filenames:
                if os.path.isfile(user_config_filename):
                    override_config = ConfigObj(infile=user_config_filename, configspec=config_specification)
                    config.merge(override_config)
                    break

        # read configuration from environment variables
        for key, val in os.environ.items():
            if key[0:7] == 'CONFIG.':
                DictUtil.nested_set(config, key[7:], val)

        # merge extra configuration
        if extra_config is None:
            extra_config={}
        config.merge(extra_config)

        if config == {}:
            config_files = [ DEFAULT_CONFIG_FILENAME ]
            if user_config_filenames is not None:
                config_files += list( user_config_filenames )
            raise ValueError("No configuration data provided by {}"
                " or environment variables.".format( ', '.join(config_files) ))

        # validate configuration against schema
        validator = Validator()
        validator.functions['any'] = ConfigFromFilesAndEnv.any_checker
        result = config.validate(validator, preserve_errors=True)

        if result is not True:
            raise InvalidConfigError(config, result)

        if get_extra_values(config):
            raise ExtraValuesError(config)

        return config


    @staticmethod
    def any_checker(value):
        value, _ = ConfigObj()._handle_value(value)

        # parse to integer
        try:
            return is_integer(value)
        except VdtTypeError:
            pass

        # parse to float
        try:
            return is_float(value)
        except VdtTypeError:
            pass

        # parse to bool
        try:
            return is_boolean(value)
        except VdtTypeError:
            pass

        # parse to list
        try:
            return [any_checker(val) for val in is_list(value)]
        except VdtTypeError:
            pass

        # parse to string
        return is_string(value)


class InvalidConfigError(Exception):
    """ Represents an error due to reading an invalid configuration that doesn't adhere to the schema

    Attributes:
        config (:obj:`configobj.ConfigObj`): configuration
        result (:obj:`dict`): dictionary of configuration errors
        msg (:obj:`str`): string representation of message
    """

    def __init__(self, config, result):
        """
        Args:
            config (:obj:`configobj.ConfigObj`): configuration
            result (:obj:`dict`): dictionary of configuration errors
        """
        self.config = config
        self.result = result

        errors = flatten_errors(config, result)

        # create readable error message
        messages = []

        for error in errors:
            section_list, key, exception = error

            if key is not None:
                section_list.append(key)
            else:
                section_list.append('[missing section]')

            if exception == False:
                message = ('.'.join(section_list)) + ' :: ' + 'Missing value or section'
            else:
                message = ('.'.join(section_list)) + ' :: ' + str(exception)

            messages.append(message)

        self.msg = '\n'.join(messages)

    def __str__(self):
        """ Get string representation of error 

        Returns:
            :obj:`str`: string representation of error
        """
        return self.msg


class ExtraValuesError(Exception):
    """ Represents an error due to extra configuration that is not part of the schema

    Attributes:
        config (:obj:`configobj.ConfigObj`): configuration
        msg (:obj:`str`): string representation of message
    """

    def __init__(self, config):
        """
        Args:
            config (:obj:`configobj.ConfigObj`): configuration
        """
        self.config = config

        messages = []
        for section_list, name in get_extra_values(config):

            # this code gets the extra values themselves
            the_section = config
            for section in section_list:
                the_section = config[section]

            # the_value may be a section or a value
            the_value = the_section[name]

            section_or_value = 'value'
            if isinstance(the_value, dict):
                # Sections are subclasses of dict
                section_or_value = 'section'

            section_string = ', '.join(section_list) or "top level"
            messages.append("Extra entry in section '{:s}'. Entry '{}' is a {:s}.".format(
                section_string, name, section_or_value))

        self.msg = '\n'.join(messages)

    def __str__(self):
        """ Get string representation of error

        Returns:
            :obj:`str`: string representation of error
        """
        return self.msg

