""" Info/debugging log tests

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-28
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import io
import os
import shutil
import sys
import tempfile
import types
import unittest
import wc_utils
import yaml
from capturer import CaptureOutput
from log.handlers import FileHandler, StreamHandler
from log.levels import LogLevel
from tests.config.fixtures.paths import debug_logs as debug_logs_default_paths
from wc_utils.config.core import ConfigManager
from wc_utils.debug_logs.core import DebugLogsManager
from wc_utils.debug_logs.config import LoggerConfigurator, ConfigurationError


class CheckForEnum34Test(unittest.TestCase):

    # todo: move to log's unittests
    def test_enum34(self):
        self.assertFalse(isinstance(LogLevel.DEBUG, int), msg="Install enum34 for enum compatibility "
                         "in Python < 3.4")


class DefaultDebugLogsTest(unittest.TestCase):

    def setUp(self):
        log_config = ConfigManager(debug_logs_default_paths).get_config()
        self.debug_log_manager = DebugLogsManager()
        self.debug_log_manager.setup_logs(log_config)

    def test_file(self):
        logger = self.debug_log_manager.get_log('wc.debug.file')

        handler = next(iter(logger.handlers))
        filename = handler.fh.name

        prev_size = os.path.getsize(filename)

        msg = 'debug message'
        logger.debug(msg)

        with open(filename, 'r') as file:
            file.seek(prev_size)
            new_log = file.read()

        self.assertRegex(new_log, r'^.+?; .+?; .+?; .+?:.+?:\d+; {:s}\n$'.format(msg))

        # test str(DebugLogsManager())
        self.assertIn(filename, str(self.debug_log_manager))
        self.assertIn('level', str(self.debug_log_manager))
        debug_log_manager = DebugLogsManager()
        self.assertEqual('No logs configured', str(debug_log_manager))

    def test_console(self):
        logger = self.debug_log_manager.get_log('wc.debug.console')

        msg = 'wc.debug.console message'

        # using redirect_stdout does not work with either nosetests or pytest; unclear why
        # if running with nosetests must use --nocapture, and not use --with-xunit
        # you can '> /dev/null' if stdout is bothersome
        with CaptureOutput() as capturer:
            logger.debug(msg)
            logged_line = capturer.get_text()
        self.assertRegex(logged_line, r'^.+?; .+?; .+?; .+?:.+?:\d+; {:s}$'.format(msg))


class DebugFileLogTest(unittest.TestCase):

    def setUp(self):
        # create temporary file to test logging
        _, self._temp_log_file = tempfile.mkstemp(suffix='.log')

    def tearDown(self):
        # clean up test loggers and test log file
        os.remove(self._temp_log_file)

    def test_file(self):
        debug_config = {
            'formatters': {
                'default': {
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:2.1f}; {message:s}',
                },
            },
            'handlers': {
                'file': {
                    'class': 'FileHandler',
                    'filename': self._temp_log_file,
                },
            },
            'loggers': {
                '__test__.file': {
                    'level': 'DEBUG',
                    'formatters': ['default'],
                    'handlers': ['file'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }

        # setup test logger
        debug_log_manager = DebugLogsManager()
        debug_log_manager.setup_logs(debug_config)

        # get logger
        logger = debug_log_manager.get_log('__test__.file')

        # write message
        msg = 'debug message'
        logger.debug(msg)

        # assert log file created
        self.assertTrue(os.path.isfile(self._temp_log_file))

        # assert message saved to file
        with open(self._temp_log_file, 'r') as file:
            log = file.read()
        self.assertRegex(log, r'^.+?; .+?; .+?:.+?:\d+; 1.5; {:s}\n$'.format(msg))


class DebugConsoleLogTest(unittest.TestCase):

    def setUp(self):
        # create stream
        if sys.version_info > (3, 0, 0):
            stream = io.StringIO()
        else:
            stream = io.BytesIO()

        self.stream = stream

    def tearDown(self):
        # cleanup test logger and close stream
        self.stream.close()

    def test_console(self):
        # configure test logger
        debug_config = {
            'formatters': {
                'default': {
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:f}; {message:s}',
                },
            },
            'handlers': {
                'stream': {
                    'class': 'StreamHandler',
                    'stream': 'stdout',
                },
            },
            'loggers': {
                '__test__.stream': {
                    'level': 'DEBUG',
                    'formatters': ['default'],
                    'handlers': ['stream'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }

        # setup test logger
        debug_log_manager = DebugLogsManager()
        debug_log_manager.setup_logs(debug_config)

        # get console logger
        logger = debug_log_manager.get_log('__test__.stream')

        # override stream
        next(iter(logger.handlers)).stream = self.stream

        # output message
        msg = 'debug message'
        sim_time = 2.5
        logger.debug(msg, sim_time=sim_time)

        # check message is correct
        self.assertRegex(self.stream.getvalue(), r'^.+?; .+?; .+?:.+?:\d+; {:f}; {:s}\n$'.format(sim_time, msg))


class DebugErrorTest(unittest.TestCase):

    def test_no_logs(self):
        debug_log_manager = DebugLogsManager()
        with self.assertRaisesRegex(ValueError, "^No log initialized.$"):
            debug_log_manager.get_log('')

    def test_undefined_log(self):
        debug_log_manager = DebugLogsManager()
        debug_log_manager.setup_logs({})
        with self.assertRaisesRegex(ValueError, "' not found in logs '"):
            debug_log_manager.get_log('not_exists')


class TestLoggerConfigurator(unittest.TestCase):

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_from_yaml(self):
        config = {
            'formatters': {
                'default': {
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:f}; {message:s}',
                },
            },
            'handlers': {
                'stream': {
                    'class': 'StreamHandler',
                    'stream': 'stdout',
                },
            },
            'loggers': {
                'log_stream': {
                    'level': 'DEBUG',
                    'formatters': ['default'],
                    'handlers': ['stream'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        filename = os.path.join(self.dirname, 'config.yml')
        with open(filename, 'w') as file:
            file.write(yaml.dump(config))
        formatters, handlers, loggers = LoggerConfigurator.from_yaml(filename)

        self.assertEqual(len(formatters), 1)
        self.assertEqual(formatters['default'].name, 'default')
        self.assertEqual(formatters['default'].template, config['formatters']['default']['template'])

        self.assertEqual(len(handlers), 1)
        self.assertIsInstance(handlers['stream'], StreamHandler)
        self.assertEqual(handlers['stream'].name, 'stream')

        self.assertEqual(len(loggers), 1)
        self.assertEqual(loggers['log_stream'].name, 'log_stream')
        self.assertEqual(loggers['log_stream'].level, LogLevel.DEBUG)
        self.assertEqual(len(loggers['log_stream'].formatters), 1)
        self.assertEqual(list(loggers['log_stream'].formatters)[0].name, 'default')
        self.assertEqual(len(loggers['log_stream'].handlers), 1)
        self.assertEqual(list(loggers['log_stream'].handlers)[0].name, 'stream')
        self.assertEqual(loggers['log_stream'].additional_context, config['loggers']['log_stream']['additional_context'])

    def test_from_dict(self):
        filename = os.path.join(self.dirname, 'subdir', 'file.log')

        config = {
            'formatters': {
                'default': {
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:f}; {message:s}',
                },
            },
            'handlers': {
                'stream': {
                    'class': 'StreamHandler',
                    'stream': 'stdout',
                },
                'file': {
                    'class': 'FileHandler',
                    'filename': filename,
                },
            },
            'loggers': {
                'log_stream': {
                    'level': 'DEBUG',
                    'formatters': ['default'],
                    'handlers': ['stream'],
                    'additional_context': {'sim_time': 1.5},
                },
                'log_file': {
                    'level': 'DEBUG',
                    'formatters': ['default'],
                    'handlers': ['file'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        formatters, handlers, loggers = LoggerConfigurator.from_dict(config)

        self.assertEqual(len(formatters), 1)
        self.assertEqual(formatters['default'].name, 'default')
        self.assertEqual(formatters['default'].template, config['formatters']['default']['template'])

        self.assertEqual(len(handlers), 2)
        self.assertIsInstance(handlers['stream'], StreamHandler)
        self.assertEqual(handlers['stream'].name, 'stream')
        self.assertIsInstance(handlers['file'], FileHandler)
        self.assertEqual(handlers['file'].name, 'file')

        self.assertEqual(len(loggers), 2)
        self.assertEqual(loggers['log_stream'].name, 'log_stream')
        self.assertEqual(loggers['log_stream'].level, LogLevel.DEBUG)
        self.assertEqual(len(loggers['log_stream'].formatters), 1)
        self.assertEqual(list(loggers['log_stream'].formatters)[0].name, 'default')
        self.assertEqual(len(loggers['log_stream'].handlers), 1)
        self.assertEqual(list(loggers['log_stream'].handlers)[0].name, 'stream')
        self.assertEqual(loggers['log_stream'].additional_context, config['loggers']['log_stream']['additional_context'])
        self.assertEqual(loggers['log_file'].name, 'log_file')
        self.assertEqual(loggers['log_file'].level, LogLevel.DEBUG)
        self.assertEqual(len(loggers['log_file'].formatters), 1)
        self.assertEqual(list(loggers['log_file'].formatters)[0].name, 'default')
        self.assertEqual(len(loggers['log_file'].handlers), 1)
        self.assertEqual(list(loggers['log_file'].handlers)[0].name, 'file')
        self.assertEqual(loggers['log_file'].additional_context, config['loggers']['log_file']['additional_context'])

    def test_unsupported_handler_class(self):
        config = {
            'handlers': {
                'handler': {
                    'class': 'unsupported',
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, '^Unsupported handler class: '):
            LoggerConfigurator.from_dict(config)

    def test_undefined_formatter(self):
        config = {
            'formatters': {
            },
            'handlers': {
                'stream': {
                    'class': 'StreamHandler',
                    'stream': 'stdout',
                },
            },
            'loggers': {
                'log_stream': {
                    'level': 'DEBUG',
                    'formatters': ['undefined'],
                    'handlers': ['stream'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, ' not found.$'):
            LoggerConfigurator.from_dict(config)

    def test_no_level(self):
        config = {
            'formatters': {
                'default': {
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:f}; {message:s}',
                },
            },
            'handlers': {
                'stream': {
                    'class': 'StreamHandler',
                    'stream': 'stdout',
                },
            },
            'loggers': {
                'log_stream': {
                    'formatters': ['default'],
                    'handlers': ['stream'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, "^Level must be defined$"):
            LoggerConfigurator.from_dict(config)

    def test_no_formatter(self):
        config = {
            'formatters': {
            },
            'handlers': {
                'stream': {
                    'class': 'StreamHandler',
                    'stream': 'stdout',
                },
            },
            'loggers': {
                'log_stream': {
                    'level': 'DEBUG',
                    'handlers': ['stream'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, '^At least one formatter must be defined.$'):
            LoggerConfigurator.from_dict(config)

    def test_no_handler(self):
        config = {
            'formatters': {
                'default': {
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:f}; {message:s}',
                },
            },
            'handlers': {
            },
            'loggers': {
                'log_stream': {
                    'level': 'DEBUG',
                    'formatters': ['default'],
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, '^At least one handler must be defined.$'):
            LoggerConfigurator.from_dict(config)


class ApiTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(wc_utils.debug_logs, types.ModuleType)
        self.assertIsInstance(wc_utils.debug_logs.DebugLogsManager, type)
