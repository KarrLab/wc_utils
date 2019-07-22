""" Read configuration settings from files, environment variables, and function arguments

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-25
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from configobj import ConfigObj
from configobj import flatten_errors, get_extra_values
from copy import deepcopy
from pathlib import Path
from validate import Validator, is_boolean, is_float, is_integer, is_list, is_string, VdtTypeError
from wc_utils.util.dict import DictUtil
import math
import os
import pkg_resources
import six
import string
import sys


class ConfigPaths(object):
    """ Paths to configuration files and schema

    Attributes:
        default (:obj:`str`): the default config filename
        schema (:obj:`str`): the config schema filename
        user (:obj:`list`): an iterable of other config files
    """

    def __init__(self, default=None, schema=None, user=None):
        self.default = default
        self.schema = schema
        self.user = user or ()

    def deepcopy(self):
        """ Returns a deep copy of the object

        Returns:
            :obj:`ConfigPaths`: deep copy of the object
        """
        return deepcopy(self)


class ConfigManager(object):
    """Obtain configuration information from ini files, environment variables, and/or function arguments.

    Load configuration information from an ini format file, environment variables, and/or function arguments.
    Validate the configuration against a configuration schema. Return the configuration
    as a nested dictionary.

    Optionally, configuration values can be templates for substitution with :obj:`string.Template`.

    Attributes:
        paths (:obj:`ConfigPaths`): paths to configuration files and schema
    """

    def __init__(self, paths=None):
        self.paths = paths

    def get_config(self, extra=None, context=None):
        """ Setup configuration from config file(s), environment variables, and/or function arguments.

        1. Setup configuration from default values specified in `paths.default`.
        2. If `paths.user` is set, find the first file in it that exists, and override
           the default configuration with the values specified in the file.
        3. Override configuration with values from environment variables. Environment variables
           can be set with the following syntax::

               CONFIG.level1.level2...=val

        4. Override configuration with additional configuration in `extra`.
        5. Substitute context into templates
        6. Validate configuration against the schema specified in `paths.schema`.

        Args:
            extra (:obj:`dict`, optional): additional configuration to override
            context (:obj:`dict`, optional): context for template substitution

        Returns:
            :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the configuration source(s).

        Raises:
            :obj:`InvalidConfigError`: if configuration doesn't validate against schema
            :obj:`ValueError`: if no configuration is found
        """

        # read configuration schema/specification
        config_specification = ConfigObj(self.paths.schema, list_values=False, _inspec=True)

        # read default configuration
        value_sources = []
        if os.path.isfile(self.paths.default):
            value_sources.append(self.paths.default)
        config = ConfigObj(infile=self.paths.default, configspec=config_specification)
        self.validate(config, value_sources)

        # read user's configuration files
        for user_config_filename in self.paths.user:
            if os.path.isfile(user_config_filename):
                override_config = ConfigObj(infile=user_config_filename, configspec=config_specification)
                config.merge(override_config)
                self.validate(config, [user_config_filename])
                break

        # read configuration from environment variables
        value_sources = []
        for key, val in os.environ.items():
            if key.startswith('CONFIG__DOT__'):
                nested_keys = key[13:].split('__DOT__')
                if nested_keys[0] in config:
                    DictUtil.nested_set(config, nested_keys, val)
                    value_sources.append("Environment variable '{}'".format(key))
        self.validate(config, value_sources)

        # merge extra configuration
        if extra is None:
            extra = {}
        else:
            config.merge(extra)
            self.validate(config, ["'extra' argument"])

        # ensure that a configuration is found
        if not config:
            raise ValueError(("No configuration found in:\n"
                              "  Default path: {}\n"
                              "  User paths: {}\n"
                              "  Extras: {}\n"
                              "  Environment variables"
                              ).format(
                self.paths.default, ', '.join(self.paths.user), extra))

        # perform template substitution
        to_sub = [config]
        while to_sub:
            dictionary = to_sub.pop()
            keys = list(dictionary.keys())
            for key in keys:
                val = dictionary[key]
                key2 = string.Template(key).substitute(context)

                val2 = val
                if isinstance(val, dict):
                    to_sub.append(val)
                elif isinstance(val, (list, tuple)):
                    val2 = [string.Template(v).substitute(context) for v in val]
                elif isinstance(val, six.string_types):
                    val2 = string.Template(val).substitute(context)

                dictionary.pop(key)
                dictionary[key2] = val2

        # re-validate configuration against schema after substitution
        self.validate(config, value_sources)

        # return config
        return config

    def validate(self, config, value_sources):
        """ Validate configuration

        Args:
            config (:obj:`ConfigObj`): configuration

        Raises:
            :obj:`InvalidConfigError`: if configuration doesn't validate against schema
            :obj:`ValueError`: if no configuration is found
        """
        validator = Validator()
        validator.functions['any'] = any_checker
        result = config.validate(validator, copy=True, preserve_errors=True)

        if result is not True:
            raise InvalidConfigError(value_sources, config, result)

        if get_extra_values(config):
            raise ExtraValuesError(value_sources, config)


def any_checker(value):
    ''' Convert value to its built-in data type if possible

    Convert a string value to its built-in data type (integer, float, boolean, str
    or list of these) if possible

    Args:
        value (:obj:`object`): a value to be converted

    Returns:
        :obj:`type`: the converted value

    Raises:
        :obj:`VdtTypeError`: if the value cannot be converted
    '''

    if not isinstance(value, float) or not math.isnan(value):
        # if statement needed because `_handle_value` doesn't seem to be able to handle nan
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
        sources (:obj:`list` of :obj:`str`): list of sources of configuration values
        config (:obj:`configobj.ConfigObj`): configuration
        result (:obj:`dict`): dictionary of configuration errors
        msg (:obj:`str`): string representation of message
    """

    def __init__(self, sources, config, result):
        """
        Args:
            sources (:obj:`list` of :obj:`str`): list of sources of configuration values
            config (:obj:`configobj.ConfigObj`): configuration
            result (:obj:`dict`): dictionary of configuration errors
        """
        self.sources = sources
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

        self.msg = ('The following configuration sources\n  {}\n\n'
                    'contain the following configuration errors\n  {}').format(
            '\n  '.join(sources), '\n  '.join(messages))

    def __str__(self):
        """ Get string representation of error

        Returns:
            :obj:`str`: string representation of error
        """
        return self.msg


class ExtraValuesError(Exception):
    """ Represents an error due to extra configuration that is not part of the schema

    Attributes:
        sources (:obj:`list` of :obj:`str`): list of sources of configuration values
        config (:obj:`configobj.ConfigObj`): configuration
        msg (:obj:`str`): string representation of message
    """

    def __init__(self, sources, config):
        """
        Args:
            sources (:obj:`list` of :obj:`str`): list of sources of configuration values
            config (:obj:`configobj.ConfigObj`): configuration
        """
        self.sources = sources
        self.config = config

        messages = []

        # todo: ensure that self.msg is generated even if this for loop raises another exception
        for section_list, name in get_extra_values(config):

            # this code gets the extra values themselves
            the_section = config
            for i_section, section in enumerate(section_list):
                if section in config:
                    the_section = config[section]
                else:
                    section_list = section_list[0:i_section]
                    name = section
                    break

            # the_value may be a section or a value
            the_value = the_section[name]

            section_or_value = 'value'
            if isinstance(the_value, dict):
                # Sections are subclasses of dict
                section_or_value = 'section'

            section_string = ', '.join(section_list) or "top level"
            messages.append("Extra entry in section '{:s}'. Entry '{}' is a {:s}.".format(
                section_string, name, section_or_value))

        self.msg = ('The following configuration sources\n  {}\n\n'
                    'contain the following configuration errors\n  {}').format(
            '\n  '.join(sources), '\n  '.join(messages))

    def __str__(self):
        """ Get string representation of error

        Returns:
            :obj:`str`: string representation of error
        """
        return self.msg


def get_config(extra=None):
    """ Get configuration

    Args:
        extra (:obj:`dict`, optional): additional configuration to override

    Returns:
        :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the configuration source(s).
    """
    paths = ConfigPaths(
        default=pkg_resources.resource_filename('wc_utils', 'config/core.default.cfg'),
        schema=pkg_resources.resource_filename('wc_utils', 'config/core.schema.cfg'),
        user=(
            'wc_utils.cfg',
            os.path.expanduser('~/.wc/wc_utils.cfg'),
        ),
    )

    return ConfigManager(paths).get_config(extra=extra)


class AltResourceName(object):
    """ Get pathname of resource file; a substitute for `pkg_resources.resource_filename`

    Finds paths to resource files in a package that cannot be imported by the standard Python
    import system.

    Usage:

    * `pkg_resources.resource_filename(package, *path_components_of_resource_in_package)
    * `AltResourceName(any_file_in_package).resource_filename(*path_components_of_resource_in_package)

    Attributes:
        package_root (:obj:`str`): root directory of a package
    """

    def __init__(self, file_in_package):
        self.package_root = self.get_package_root(file_in_package)

    @staticmethod
    def get_package_root(file_in_package):
        """ Obtain root directory of a package by following `__init__.py` files up the file hierarchy

        Args:
            file_in_package (:obj:`str`): pathname of a file in a package

        Returns:
            :obj:`str`: pathname of root of package

        Raises:
            :obj:`ValueError`: if `file_in_package` is not the pathname of a file in a package
        """
        path = Path(file_in_package)
        # go up directory hierarchy from path and get first directory that does not contain '__init__.py'
        if path.is_dir():
            dir = path
        else:
            dir = path.parent
        found_package = False
        while True:
            if not dir.joinpath('__init__.py').is_file():
                break
            # exit at / root
            if dir == dir.parent:
                break
            found_package = True
            highest_package = dir
            dir = dir.parent
        if found_package:
            return str(highest_package)
        raise ValueError("'{}' is not the pathname of a file in a package".format(file_in_package))


    def resource_filename(self, *args):
        """ Get pathname of resource file; replaces `pkg_resources.resource_filename`

        Args:
            args (:obj:`list`): pathname components of resource file

        Returns:
            :obj:`str`: pathname of resource file
        """
        return os.path.join(self.package_root, *args)
