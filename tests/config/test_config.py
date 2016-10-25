""" Test configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-25
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from validate import Validator
import configobj
import os
import sys
import tempfile
import unittest

from tests.config_files import config_constants
from wc_utils.debug_logs import config_from_files_and_env
from wc_utils.debug_logs.config_from_files_and_env import ConfigFromFilesAndEnv
from wc_utils.environ import EnvironUtils
from wc_utils.util.types import TypesUtil


class TestConfig(unittest.TestCase):

    def test_get_from_user(self):
        expected = deepcopy(ConfigFromFilesAndEnv.setup(config_constants))
        expected['log']['debug']['formatters']['__test__'] = {'template': 'xxxx', 'append_new_line': False}

        _, temp_config_filename = tempfile.mkstemp()
        with open(temp_config_filename, 'w') as file:
            file.write(u'[log]\n')
            file.write(u'    [[debug]]\n')
            file.write(u'        [[[formatters]]]\n')
            file.write(u'            [[[[__test__]]]]\n')
            file.write(u'                template = xxxx\n')
            file.write(u'                append_new_line = False\n')

        config_settings = ConfigFromFilesAndEnv._setup(config_constants.DEFAULT_CONFIG_FILENAME,
                                                       config_constants.CONFIG_SCHEMA_FILENAME,
                                                       user_config_filenames=[temp_config_filename])
        self.assertEqual(config_settings['log']['debug']['formatters'], expected['log']['debug']['formatters'])
        TypesUtil.assert_value_equal(config_settings, expected)

        os.remove(temp_config_filename)

    def test_get_from_env(self):
        expected = deepcopy(ConfigFromFilesAndEnv.setup(config_constants))
        expected['log']['debug']['formatters']['__test__'] = {'template': 'xxxx', 'append_new_line': False}

        env = {
            'CONFIG.log.debug.formatters.__test__.template': 'xxxx',
            'CONFIG.log.debug.formatters.__test__.append_new_line': 'False',
        }
        with EnvironUtils.make_temp_environ(**env):
            config_settings = ConfigFromFilesAndEnv.setup(config_constants)

        self.assertEqual(config_settings['log']['debug']['formatters'], expected['log']['debug']['formatters'])
        TypesUtil.assert_value_equal(config_settings, expected)

    def test_get_from_args(self):
        expected = deepcopy(ConfigFromFilesAndEnv.setup(config_constants))
        expected['log']['debug']['formatters']['__test__'] = {'template': 'xxxx', 'append_new_line': False}

        extra = {'log': {'debug': {'formatters': {'__test__': {'template': 'xxxx', 'append_new_line': False}}}}}
        config_settings = ConfigFromFilesAndEnv._setup(config_constants.DEFAULT_CONFIG_FILENAME,
                                                       config_constants.CONFIG_SCHEMA_FILENAME, extra_config=extra)

        self.assertEqual(config_settings['log']['debug']['formatters'], expected['log']['debug']['formatters'])
        TypesUtil.assert_value_equal(config_settings, expected)

    def test_extra_config(self):
        # test to __str__
        config_specification = configobj.ConfigObj(config_constants.CONFIG_SCHEMA_FILENAME,
                                                   list_values=False, _inspec=True)
        config = configobj.ConfigObj(configspec=config_specification)
        config.merge({'__extra__': True})
        validator = Validator()
        result = config.validate(validator, preserve_errors=True)
        if configobj.get_extra_values(config):
            str(config_from_files_and_env.ExtraValuesError(config))
        else:
            raise Exception('Error not raised')

        # extra section
        self.assertRaises(config_from_files_and_env.ExtraValuesError,
                          lambda: ConfigFromFilesAndEnv._setup(config_constants.DEFAULT_CONFIG_FILENAME,
                                                               config_constants.CONFIG_SCHEMA_FILENAME,
                                                               {'__extra__': True}))

        # extra subsection, extra key
        self.assertRaises(config_from_files_and_env.ExtraValuesError, lambda: ConfigFromFilesAndEnv._setup(
            config_constants.DEFAULT_CONFIG_FILENAME,
            config_constants.CONFIG_SCHEMA_FILENAME,
            {'log': {'__extra__': True, '__extra__2': {'val': 'is_dict'}}}))

    def test_invalid_config(self):
        # missing section
        config_specification = configobj.ConfigObj(config_constants.CONFIG_SCHEMA_FILENAME,
                                                   list_values=False, _inspec=True)
        config_specification.merge({'__test__': {'enabled': 'boolean()'}})
        config = configobj.ConfigObj(configspec=config_specification)
        validator = Validator()
        result = config.validate(validator, preserve_errors=True)
        if result is not True:
            str(config_from_files_and_env.InvalidConfigError(config, result))
        else:
            raise Exception('Error not raised')

        # incorrect type
        self.assertRaises(config_from_files_and_env.InvalidConfigError,
                          lambda: ConfigFromFilesAndEnv._setup(
                              config_constants.DEFAULT_CONFIG_FILENAME,
                              config_constants.CONFIG_SCHEMA_FILENAME,
                              {'log': {'debug': {'formatters':
                                                 {'__test__': {'template': '', 'append_new_line': 10}}}}}))

        # missing value
        self.assertRaises(config_from_files_and_env.InvalidConfigError,
                          lambda: ConfigFromFilesAndEnv._setup(
                              config_constants.DEFAULT_CONFIG_FILENAME,
                              config_constants.CONFIG_SCHEMA_FILENAME,
                              {'log': {'debug': {'loggers':
                                                 {'__test__': {'formatters': ['default']}}}}}))

    def test_any_checker(self):
        validator = Validator()
        validator.functions['any'] = ConfigFromFilesAndEnv.any_checker

        # Boolean: True
        self.assertIsInstance(validator.check('any', 'True'), bool)
        self.assertEqual(validator.check('any', 'True'), True)
        self.assertEqual(validator.check('any', 'yes'), True)

        # Boolean: False
        self.assertIsInstance(validator.check('any', 'False'), bool)
        self.assertEqual(validator.check('any', 'False'), False)
        self.assertEqual(validator.check('any', 'no'), False)

        # integers
        self.assertIsInstance(validator.check('any', '2'), int)
        self.assertEqual(validator.check('any', '2'), 2)

        # float
        self.assertIsInstance(validator.check('any', '2.1'), float)
        self.assertEqual(validator.check('any', '2.1'), 2.1)

        # lists
        self.assertEquals(validator.check('any', ','), [])
        self.assertEquals(validator.check('any', '1,'), [1])
        self.assertEquals(validator.check('any', '1,2'), [1, 2])
        self.assertEquals(validator.check('any', '1,false'), [1, False])
        self.assertEquals(validator.check('any', '1,false, string'), [1, False, 'string'])
        self.assertEquals(validator.check('any', '1,false, string, 2.1'), [1, False, 'string', 2.1])
        TypesUtil.assert_value_equal(validator.check('any', '1,false, string, 2.1, nan'),
                                     [1, False, 'string', 2.1, float('nan')])

        # string
        self.assertIsInstance(validator.check('any', 'string'), str)
        self.assertEqual(validator.check('any', 'string'), 'string')
