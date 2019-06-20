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
from logging2 import FileHandler, StdOutHandler, LogLevel
from tests.config.fixtures.paths import debug_logs as debug_logs_default_paths
from wc_utils.config.core import ConfigManager
from wc_utils.debug_logs.core import DebugLogsManager
from wc_utils.debug_logs.config import LoggerConfigurator, ConfigurationError


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
            'handlers': {
                'file': {
                    'class': 'FileHandler',
                    'filename': self._temp_log_file,
                    'level': 'debug',
                },
            },
            'loggers': {
                '__test__.file': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:2.1f}; {message:s}',
                    'handler': 'file',
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
            'handlers': {
                'stream': {
                    'class': 'StdOutHandler',
                    'level': 'debug',
                },
            },
            'loggers': {
                '__test__.stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'stream',
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
            'handlers': {
                'stream': {
                    'class': 'StdOutHandler',
                    'level': 'debug',
                },
            },
            'loggers': {
                'log_stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'stream',
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        filename = os.path.join(self.dirname, 'config.yml')
        with open(filename, 'w') as file:
            file.write(yaml.dump(config))
        handlers, loggers = LoggerConfigurator.from_yaml(filename)

        self.assertEqual(len(handlers), 1)
        self.assertIsInstance(handlers['stream'], StdOutHandler)
        self.assertEqual(handlers['stream'].name, 'stream')
        self.assertEqual(handlers['stream'].min_level, LogLevel.debug)

        self.assertEqual(len(loggers), 1)
        self.assertEqual(loggers['log_stream'].name, 'log_stream')
        self.assertEqual(loggers['log_stream'].template, config['loggers']['log_stream']['template'])
        self.assertEqual(len(loggers['log_stream'].handlers), 1)
        self.assertEqual(list(loggers['log_stream'].handlers)[0].name, 'stream')
        self.assertEqual(loggers['log_stream'].additional_context, config['loggers']['log_stream']['additional_context'])

    def test_from_dict(self):
        filename = os.path.join(self.dirname, 'subdir', 'file.log')

        config = {
            'handlers': {
                'stream': {
                    'class': 'StdOutHandler',
                    'level': 'debug',
                },
                'file': {
                    'class': 'FileHandler',
                    'filename': filename,
                    'level': 'debug',
                },
            },
            'loggers': {
                'log_stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'stream',
                    'additional_context': {'sim_time': 1.5},
                },
                'log_file': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'file',
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        handlers, loggers = LoggerConfigurator.from_dict(config)

        self.assertEqual(len(handlers), 2)
        self.assertIsInstance(handlers['stream'], StdOutHandler)
        self.assertEqual(handlers['stream'].name, 'stream')
        self.assertEqual(handlers['stream'].min_level, LogLevel.debug)
        self.assertIsInstance(handlers['file'], FileHandler)
        self.assertEqual(handlers['file'].name, 'file')
        self.assertEqual(handlers['file'].min_level, LogLevel.debug)

        self.assertEqual(len(loggers), 2)
        self.assertEqual(loggers['log_stream'].name, 'log_stream')
        self.assertEqual(loggers['log_stream'].template, config['loggers']['log_stream']['template'])
        self.assertEqual(len(loggers['log_stream'].handlers), 1)
        self.assertEqual(list(loggers['log_stream'].handlers)[0].name, 'stream')
        self.assertEqual(loggers['log_stream'].additional_context, config['loggers']['log_stream']['additional_context'])
        self.assertEqual(loggers['log_file'].name, 'log_file')
        self.assertEqual(loggers['log_file'].template, config['loggers']['log_file']['template'])
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

    def test_no_level(self):
        config = {
            'handlers': {
                'stream': {
                    'class': 'StdOutHandler',
                },
            },
            'loggers': {
                'log_stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'stream',
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        handlers, loggers = LoggerConfigurator.from_dict(config)
        self.assertEqual(handlers['stream'].min_level, LogLevel.debug)

    def test_no_handler(self):
        config = {
            'handlers': {
            },
            'loggers': {
                'log_stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, '^A handler must be defined.$'):
            LoggerConfigurator.from_dict(config)

    def test_extra_handler_options(self):
        config = {
            'handlers': {
                'stream': {
                    'class': 'StdOutHandler',
                    'extra_option': 'extra_value',
                },
            },
            'loggers': {
                'log_stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'stream',
                    'additional_context': {'sim_time': 1.5},
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, '^Handler configuration does not support options'):
            LoggerConfigurator.from_dict(config)

    def test_extra_logger_options(self):
        config = {
            'handlers': {
                'stream': {
                    'class': 'StdOutHandler',
                },
            },
            'loggers': {
                'log_stream': {
                    'template': '{timestamp}; {name:s}; {level:s}; {source}:{function:s}:{line:d}; {sim_time:f}; {message:s}',
                    'handler': 'stream',
                    'additional_context': {'sim_time': 1.5},
                    'extra_option': 'extra_value',
                },
            },
        }
        with self.assertRaisesRegex(ConfigurationError, '^Logger configuration does not support options'):
            LoggerConfigurator.from_dict(config)


class ApiTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(wc_utils.debug_logs, types.ModuleType)
        self.assertIsInstance(wc_utils.debug_logs.DebugLogsManager, type)
