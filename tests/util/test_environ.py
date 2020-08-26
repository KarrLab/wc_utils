""" Test EnvironUtils

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-24
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from wc_utils.util.environ import EnvironUtils, ConfigEnvDict
import os
import unittest


class TestEnvironUtils(unittest.TestCase):

    def test_mktemp(self):
        path = os.getenv('PATH')

        self.assertNotEqual(path, 'test')
        with EnvironUtils.make_temp_environ(PATH='test'):
            self.assertEqual(os.getenv('PATH'), 'test')
        self.assertEqual(os.getenv('PATH'), path)

        self.assertTrue('NO_SUCH_ENV_VAR' not in os.environ)
        with EnvironUtils.make_temp_environ(NO_SUCH_ENV_VAR='test_value'):
            self.assertEqual(os.environ['NO_SUCH_ENV_VAR'], 'test_value')
        self.assertTrue('NO_SUCH_ENV_VAR' not in os.environ)


class TestConfigEnvDict(unittest.TestCase):
    # Note: Use of TestConfigEnvDict for configuration variables is tested in test_config.py::TestConfig::test_get_from_env

    def test(self):
        config_env_dict = ConfigEnvDict()
        config_env_dict.add_config_value(['repo', 'level'], 'value')
        dict_1 = {''.join(['CONFIG', '__DOT__', 'repo', '__DOT__', 'level']): 'value'}
        self.assertEqual(config_env_dict.get_env_dict(), dict_1)
        config_env_dict.add_config_value(['repo_2'], 'value2')
        dict_2 = {''.join(['CONFIG', '__DOT__', 'repo_2']): 'value2'}
        dict_1.update(dict_2)
        self.assertEqual(config_env_dict.get_env_dict(), dict_1)

        tmp_conf = ConfigEnvDict().prep_tmp_conf(((['repo', 'level'], 'value'),
                                                  (['repo_2'], 'value2')))
        self.assertEqual(tmp_conf, dict_1)

        with self.assertRaises(ValueError):
            ConfigEnvDict().prep_tmp_conf([(['repo', 'level'], 5)])
