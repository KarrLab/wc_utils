""" Test configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-25
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

from tests.config.fixtures.paths import debug_logs as debug_logs_default_paths
from wc_utils.config.core import ConfigManager, any_checker, ExtraValuesError, InvalidConfigError
from wc_utils.util.environ import EnvironUtils
from wc_utils.util.types import assert_value_equal


class TestConfig(unittest.TestCase):

    def test_get_from_user(self):
        expected = ConfigManager(debug_logs_default_paths).get_config()
        expected['debug_logs']['formatters']['__test__'] = {'template': 'xxxx', 'append_new_line': False}

        _, temp_config_filename = tempfile.mkstemp()
        with open(temp_config_filename, 'w') as file:
            file.write(u'[debug_logs]\n')
            file.write(u'    [[formatters]]\n')
            file.write(u'        [[[__test__]]]\n')
            file.write(u'            template = xxxx\n')
            file.write(u'            append_new_line = False\n')

        temp_paths = deepcopy(debug_logs_default_paths)
        temp_paths.user = [temp_config_filename]
        config_settings = ConfigManager(temp_paths).get_config()

        self.assertEqual(config_settings['debug_logs']['formatters'], expected['debug_logs']['formatters'])
        assert_value_equal(config_settings, expected)

        os.remove(temp_config_filename)

    def test_get_from_env(self):
        expected = ConfigManager(debug_logs_default_paths).get_config()
        expected['debug_logs']['formatters']['__test__'] = {'template': 'xxxx', 'append_new_line': False}

        env = {
            'CONFIG.debug_logs.formatters.__test__.template': 'xxxx',
            'CONFIG.debug_logs.formatters.__test__.append_new_line': 'False',
        }
        with EnvironUtils.make_temp_environ(**env):
            config_settings = ConfigManager(debug_logs_default_paths).get_config()

        self.assertEqual(config_settings['debug_logs']['formatters'], expected['debug_logs']['formatters'])
        assert_value_equal(config_settings, expected)

    def test_get_from_args(self):
        expected = ConfigManager(debug_logs_default_paths).get_config()
        expected['debug_logs']['formatters']['__test__'] = {'template': 'xxxx', 'append_new_line': False}

        extra = {'debug_logs': {'formatters': {'__test__': {'template': 'xxxx', 'append_new_line': False}}}}
        config_settings = ConfigManager(debug_logs_default_paths).get_config(extra=extra)

        self.assertEqual(config_settings['debug_logs']['formatters'], expected['debug_logs']['formatters'])
        assert_value_equal(config_settings, expected)

    def test_extra(self):
        # test to __str__
        config_specification = configobj.ConfigObj(debug_logs_default_paths.schema,
                                                   list_values=False, _inspec=True)
        config = configobj.ConfigObj(configspec=config_specification)
        config.merge({'__extra__': True})
        validator = Validator()
        result = config.validate(validator, preserve_errors=True)
        if configobj.get_extra_values(config):
            str(ExtraValuesError(config))
        else:
            raise Exception('Error not raised')

        # extra section
        extra = {'__extra__': True}
        self.assertRaises(ExtraValuesError,
                          lambda: ConfigManager(debug_logs_default_paths).get_config(extra))

        # extra subsection, extra key
        extra = {
            'debug_logs': {
                '__extra__': True,
                '__extra__2': {
                    'val': 'is_dict'
                }
            }
        }
        self.assertRaises(ExtraValuesError,
                          lambda: ConfigManager(debug_logs_default_paths).get_config(extra))

    def test_invalid_config(self):
        # missing section
        config_specification = configobj.ConfigObj(debug_logs_default_paths.schema,
                                                   list_values=False, _inspec=True)
        config_specification.merge({'__test__': {'enabled': 'boolean()'}})
        config = configobj.ConfigObj(configspec=config_specification)
        validator = Validator()
        result = config.validate(validator, preserve_errors=True)
        if result is not True:
            str(InvalidConfigError(config, result))
        else:
            raise Exception('Error not raised')

        # incorrect type
        extra = {
            'debug_logs': {
                'formatters': {
                    '__test__': {
                        'template': '',
                        'append_new_line': 10,
                    }
                }
            }
        }
        self.assertRaises(InvalidConfigError,
                          lambda: ConfigManager(debug_logs_default_paths).get_config(extra))

        # missing value
        extra = {
            'debug_logs': {
                'loggers': {
                    '__test__': {
                        'formatters': ['default']
                    }
                }
            }
        }
        self.assertRaises(InvalidConfigError,
                          lambda: ConfigManager(debug_logs_default_paths).get_config(extra))

    def test_any_checker(self):
        validator = Validator()
        validator.functions['any'] = any_checker

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
        assert_value_equal(validator.check('any', '1,false, string, 2.1, nan'),
                                     [1, False, 'string', 2.1, float('nan')])

        # string
        self.assertIsInstance(validator.check('any', 'string'), str)
        self.assertEqual(validator.check('any', 'string'), 'string')
