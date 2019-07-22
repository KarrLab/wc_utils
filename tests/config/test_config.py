""" Test configuration

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-08-25
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from copy import deepcopy
from validate import Validator
import configobj
import mock
import os
import re
import shutil
import sys
import tempfile
import pkg_resources
import types
import unittest
import wc_utils

from tests.config.fixtures.paths import debug_logs as debug_logs_default_paths
from wc_utils.config.core import (ConfigManager, ConfigPaths, any_checker,
                                  ExtraValuesError, InvalidConfigError, get_config,
                                  AltResourceName)
from wc_utils.util.environ import EnvironUtils, MakeEnvironArgs
from wc_utils.util.types import assert_value_equal


class TestConfig(unittest.TestCase):

    def test_get_from_user(self):
        expected = ConfigManager(debug_logs_default_paths).get_config()
        expected['debug_logs']['loggers']['__test__'] = {
            'template': 'xxxx',
            'handler': 'MyHandler',
            'timezone': None,
            'additional_context': {},
        }

        _, temp_config_filename = tempfile.mkstemp()
        with open(temp_config_filename, 'w') as file:
            file.write(u'[debug_logs]\n')
            file.write(u'    [[loggers]]\n')
            file.write(u'        [[[__test__]]]\n')
            file.write(u'            template = xxxx\n')
            file.write(u'            handler = MyHandler\n')

        temp_paths = deepcopy(debug_logs_default_paths)
        temp_paths.user = [temp_config_filename]
        config_settings = ConfigManager(temp_paths).get_config()

        self.assertEqual(config_settings['debug_logs']['loggers']['__test__'], expected['debug_logs']['loggers']['__test__'])
        assert_value_equal(config_settings, expected)

        os.remove(temp_config_filename)

    def test_get_from_env(self):
        expected = ConfigManager(debug_logs_default_paths).get_config()
        expected['debug_logs']['loggers']['__test__'] = {
            'template': 'xxxx',
            'timezone': None,
            'handler': 'MyHandler',
            'additional_context': {}}

        make_environ_args = MakeEnvironArgs()
        make_environ_args.add_to_env(['debug_logs', 'loggers', '__test__', 'template'], 'xxxx')
        make_environ_args.add_to_env(['debug_logs', 'loggers', '__test__', 'handler'], 'MyHandler')
        env = make_environ_args.get_env()
        with EnvironUtils.make_temp_environ(**env):
            config_settings = ConfigManager(debug_logs_default_paths).get_config()

        self.assertEqual(config_settings['debug_logs']['loggers']['__test__'], expected['debug_logs']['loggers']['__test__'])
        assert_value_equal(config_settings, expected)

    def test_get_from_args(self):
        expected = ConfigManager(debug_logs_default_paths).get_config()
        expected['debug_logs']['loggers']['__test__'] = {
            'template': 'xxxx',
            'handler': 'MyHandler',
            'timezone': None,
            'additional_context': {}}

        extra = {'debug_logs': {'loggers': {'__test__': {
            'template': 'xxxx',
            'handler': 'MyHandler',
        }}}}
        config_settings = ConfigManager(debug_logs_default_paths).get_config(extra=extra)

        self.assertEqual(config_settings['debug_logs']['loggers']['__test__'], expected['debug_logs']['loggers']['__test__'])
        assert_value_equal(config_settings, expected)

    def test_alter_directly(self):
        # use this approach to directly alter configuration values when testing, especially
        # when configuration data is loaded by many modules.
        # suppose you want to test multiple values of append_new_line
        expected = ConfigManager(debug_logs_default_paths).get_config()
        initial_handler = expected['debug_logs']['loggers']['wc.debug.file']['handler']
        self.assertEqual(initial_handler, 'debug.file')

        # override an option
        expected['debug_logs']['loggers']['wc.debug.file']['handler'] = 'MyHandler'

        # verify that this doesn't override the configuration in the config files
        current = ConfigManager(debug_logs_default_paths).get_config()
        self.assertEqual(current['debug_logs']['loggers']['wc.debug.file']['handler'], initial_handler)

    def test_template_substitution(self):
        _, schema_filename = tempfile.mkstemp()
        with open(schema_filename, 'w') as file:
            file.write(u'[sec]\n')
            file.write(u'   attr_1 = string(default=xyx)\n')
            file.write(u'   attr_2 = string(default=${root}/uvw)\n')
            file.write(u'   attr_3 = list()\n')
            file.write(u'   attr_4 = list(default=list("a", "${root}/abc", "c"))\n')
            file.write(u'   attr_5 = boolean(default=true)\n')
            file.write(u'   attr_6 = string()\n')
            file.write(u'   [[__many__]]\n')
            file.write(u'       val = string()\n')

        _, default_filename = tempfile.mkstemp()
        with open(default_filename, 'w') as file:
            file.write(u'[sec]\n')
            file.write(u'   attr_1 = ${root}/xyz\n')
            file.write(u'   attr_3 = ${root}/xyz, xyz/${root}\n')
            file.write(u'   attr_5 = False\n')
            file.write(u'   attr_6 = $${root}\n')
            file.write(u'   [[subsec-1-${root}]]\n')
            file.write(u'       val = 1-${root}\n')
            file.write(u'   [[subsec-2-${root}]]\n')
            file.write(u'       val = 2-${root}\n')

        paths = mock.Mock(schema=schema_filename, default=default_filename, user=[])
        config = ConfigManager(paths).get_config(context={'root': 'ABC'})

        self.assertEqual(config['sec']['attr_1'], 'ABC/xyz')
        self.assertEqual(config['sec']['attr_2'], 'ABC/uvw')
        self.assertEqual(config['sec']['attr_3'], ['ABC/xyz', 'xyz/ABC'])
        self.assertEqual(config['sec']['attr_4'], ['a', 'ABC/abc', 'c'])
        self.assertEqual(config['sec']['attr_5'], False)
        self.assertEqual(config['sec']['attr_6'], '${root}')
        self.assertEqual(config['sec']['subsec-1-ABC']['val'], '1-ABC')
        self.assertEqual(config['sec']['subsec-2-ABC']['val'], '2-ABC')

        os.remove(schema_filename)
        os.remove(default_filename)

    def test_template_substitution_invalid(self):
        _, schema_filename = tempfile.mkstemp()
        with open(schema_filename, 'w') as file:
            file.write(u'[sec]\n')
            file.write(u'   attr_1 = string(max=7)\n')

        _, default_filename = tempfile.mkstemp()
        with open(default_filename, 'w') as file:
            file.write(u'[sec]\n')
            file.write(u'   attr_1 = ${root}\n')

        paths = mock.Mock(schema=schema_filename, default=default_filename, user=[])
        with self.assertRaisesRegex(InvalidConfigError, 'is too long'):
            config = ConfigManager(paths).get_config(context={'root': 'a long root more than 7 chars'})

        os.remove(schema_filename)
        os.remove(default_filename)

    def test_extra(self):
        # test to __str__
        config_specification = configobj.ConfigObj(debug_logs_default_paths.schema,
                                                   list_values=False, _inspec=True)
        config = configobj.ConfigObj(configspec=config_specification)
        config.merge({'__extra__': True})
        validator = Validator()
        result = config.validate(validator, preserve_errors=True)
        self.assertNotEqual(configobj.get_extra_values(config), None)

        # extra section
        extra = {'__extra__': True}

        with self.assertRaisesRegex(ExtraValuesError, "The following configuration sources"):
            ConfigManager(debug_logs_default_paths).get_config(extra)

        with self.assertRaisesRegex(ExtraValuesError, "  'extra' argument"):
            ConfigManager(debug_logs_default_paths).get_config(extra)

        with self.assertRaisesRegex(ExtraValuesError, "Extra entry in section 'top level'. Entry '__extra__' is a value"):
            ConfigManager(debug_logs_default_paths).get_config(extra)

        # extra subsection, extra key
        extra = {
            'debug_logs': {
                '__extra__': True,
                '__extra__2': {
                    'val': 'is_dict'
                }
            }
        }
        with self.assertRaisesRegex(ExtraValuesError, "Entry '__extra__2' is a section"):
            ConfigManager(debug_logs_default_paths).get_config(extra)

    def test_extra_2(self):
        tempdir = tempfile.mkdtemp()

        schema_path = os.path.join(tempdir, 'schema.cfg')
        with open(schema_path, 'w') as file:
            file.write('[section1]\n')
            file.write('    attr_1 = integer()\n')
            file.write('    [[section2]]\n')
            file.write('        attr_2 = integer()\n')

        default_path = os.path.join(tempdir, 'default.cfg')
        with open(default_path, 'w') as file:
            file.write('[section1]\n')
            file.write('    attr_1 = 1\n')
            file.write('    [[section2]]\n')
            file.write('        attr_2 = 2\n')

        user_path = os.path.join(tempdir, 'user.cfg')
        with open(user_path, 'w') as file:
            file.write('[section1]\n')
            file.write('    attr_1 = 2\n')
            file.write('    [[section3]]\n')
            file.write('        attr_3 = 3\n')

        cfg_mgr = ConfigManager(ConfigPaths(schema=schema_path, default=default_path, user=(user_path,)))
        with self.assertRaisesRegex(ExtraValuesError, "Extra entry in section 'section1'. Entry 'section3' is a section."):
            cfg_mgr.get_config(extra={})

        user_path = os.path.join(tempdir, 'user.cfg')
        with open(user_path, 'w') as file:
            file.write('[section1]\n')
            file.write('    [[section2]]\n')
            file.write('        attr_2 = 3\n')
            file.write('    attr_1 = 2\n')

        cfg_mgr = ConfigManager(ConfigPaths(schema=schema_path, default=default_path, user=(user_path,)))
        with self.assertRaisesRegex(ExtraValuesError, "Extra entry in section 'section1'. Entry 'section2' is a section."):
            cfg_mgr.get_config(extra={})

        shutil.rmtree(tempdir)

    def test_invalid_config(self):
        # missing section
        config_specification = configobj.ConfigObj(debug_logs_default_paths.schema,
                                                   list_values=False, _inspec=True)
        config_specification.merge({'__test__': {'enabled': 'boolean()'}})
        config = configobj.ConfigObj(configspec=config_specification)
        validator = Validator()
        result = config.validate(validator, preserve_errors=True)
        InvalidConfigError([], config, result)
        self.assertNotEqual(result, True)

        # incorrect type
        extra = {
            'debug_logs': {
                'handlers': {
                    '__test__': {
                        'class': 'NotAnOption',
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
                        'template': '{source}'
                    }
                }
            }
        }
        self.assertRaises(InvalidConfigError,
                          lambda: ConfigManager(debug_logs_default_paths).get_config(extra))

    def test_no_config(self):
        file, filename = tempfile.mkstemp(suffix='.cfg')
        os.close(file)

        config_paths = ConfigPaths(schema=filename, default=filename, user=())

        with self.assertRaisesRegex(ValueError, '^No configuration found in:'):
            ConfigManager(config_paths).get_config()

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
        self.assertEqual(validator.check('any', ','), [])
        self.assertEqual(validator.check('any', '1,'), [1])
        self.assertEqual(validator.check('any', '1,2'), [1, 2])
        self.assertEqual(validator.check('any', '1,false'), [1, False])
        self.assertEqual(validator.check('any', '1,false, string'), [1, False, 'string'])
        self.assertEqual(validator.check('any', '1,false, string, 2.1'), [1, False, 'string', 2.1])
        assert_value_equal(validator.check('any', '1,false, string, 2.1, nan'),
                           [1, False, 'string', 2.1, float('nan')])

        # string
        self.assertIsInstance(validator.check('any', 'string'), str)
        self.assertEqual(validator.check('any', 'string'), 'string')

    def test_get_config(self):
        self.assertIsInstance(get_config(), configobj.ConfigObj)


class ApiTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(wc_utils.config, types.ModuleType)
        self.assertIsInstance(wc_utils.config.ConfigPaths, type)


class TestAltResourceName(unittest.TestCase):

    def test(self):

        with tempfile.TemporaryDirectory() as tmp_dir:
            with tempfile.TemporaryDirectory(dir=tmp_dir) as nested_tmp_dir:
                # test exceptions
                with self.assertRaisesRegex(ValueError, "is not the pathname of a file in a package"):
                    AltResourceName.get_package_root(nested_tmp_dir)
                with tempfile.NamedTemporaryFile(dir=nested_tmp_dir) as fp:
                    with self.assertRaises(ValueError):
                        AltResourceName.get_package_root(fp.name)

                    # create __init__.py & find package
                    open(os.path.join(nested_tmp_dir, '__init__.py'), 'a').close()
                    expected_package_root = nested_tmp_dir
                    self.assertEqual(AltResourceName.get_package_root(fp.name), expected_package_root)
                    self.assertEqual(AltResourceName.get_package_root(nested_tmp_dir), expected_package_root)

                    alt_resource_name = AltResourceName(nested_tmp_dir)
                    expected_path = fp.name
                    self.assertEqual(alt_resource_name.resource_filename(os.path.basename(fp.name)),
                        expected_path)

        # test running into '/', if it can be written
        try:
            init_in_root = os.path.join('/', '__init__.py')
            open(init_in_root, 'a').close()
            self.assertEqual(AltResourceName.get_package_root('/'), '/')
            os.remove(init_in_root)
        except Exception:
            pass

    def test_resource_filename(self):
        alt_resource_name = AltResourceName(__file__)
        expected_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'debug.default.cfg')
        self.assertEqual(expected_path,
            alt_resource_name.resource_filename('config/fixtures/debug.default.cfg'))
        self.assertEqual(expected_path,
            alt_resource_name.resource_filename('config', 'fixtures', 'debug.default.cfg'))

        # test against pkg_resources.resource_filename
        wc_utils_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        alt_resource_name = AltResourceName(os.path.join(wc_utils_repo, 'wc_utils', 'config'))
        self.assertEqual(alt_resource_name.resource_filename('VERSION'),
            pkg_resources.resource_filename('wc_utils', 'VERSION'))
