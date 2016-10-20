""" Info/debugging log tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-20
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-28
:Copyright: 2016, Karr Lab
:License: MIT
"""

import io
import os
import sys
import tempfile
import unittest
from capturer import CaptureOutput

from log.levels import LogLevel
from tests.config_files import config_constants
from wc_utils.debug_logs.config_from_files_and_env import ConfigFromFilesAndEnv
from wc_utils.debug_logs.debug import MakeLoggers
log_config = ConfigFromFilesAndEnv.setup( config_constants )
loggers = MakeLoggers().setup_logger( log_config )


class CheckForEnum34Test(unittest.TestCase):

    # todo: move to log's unittests
    def test_enum34(self):
        self.assertFalse( isinstance(LogLevel.DEBUG, int), msg="Install enum34 for enum compatibility "
            "in Python < 3.4")
 

class DefaultDebugLogsTest(unittest.TestCase):

    def test_file(self):
        logger = loggers.get_logger('wc.debug.file')

        handler = next(iter(logger.handlers))
        filename = handler.fh.name

        prev_size = os.path.getsize(filename)

        msg = 'debug message'
        logger.debug(msg)

        with open(filename, 'r') as file:
            file.seek(prev_size)
            new_log = file.read()

        self.assertRegexpMatches(new_log, '^.+?; .+?; .+?; .+?:.+?:\d+; {:s}\n$'.format(msg))

    @unittest.skip("skip, until capturer is working under pytest")
    def test_console(self):
        logger = loggers.get_logger('wc.debug.console')

        msg = 'wc.debug.console message'

        # using redirect_stdout does not work with either nosetests or pytest; unclear why
        # if running with nosetests must use --nocapture, and not use --with-xunit
        # you can '> /dev/null' if stdout is bothersome
        with CaptureOutput() as capturer:
            logger.debug(msg)
            logged_line = capturer.get_text()
        self.assertRegexpMatches(logged_line, '^.+?; .+?; .+?; .+?:.+?:\d+; {:s}$'.format(msg))


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
        loggers = MakeLoggers().setup_logger(debug_config)

        # get logger
        logger = loggers.get_logger('__test__.file')

        # write message
        msg = 'debug message'
        logger.debug(msg)

        # assert log file created
        self.assertTrue(os.path.isfile(self._temp_log_file))

        # assert message saved to file
        with open(self._temp_log_file, 'r') as file:
            log = file.read()
        self.assertRegexpMatches(log, '^.+?; .+?; .+?:.+?:\d+; 1.5; {:s}\n$'.format(msg))


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
        loggers = MakeLoggers().setup_logger(debug_config)

        # get console logger
        logger = loggers.get_logger('__test__.stream')

        # override stream
        next(iter(logger.handlers)).stream = self.stream

        # output message
        msg = 'debug message'
        sim_time=2.5
        logger.debug(msg, sim_time=sim_time)

        # check message is correct
        self.assertRegexpMatches(self.stream.getvalue(), '^.+?; .+?; .+?:.+?:\d+; {:f}; {:s}\n$'.format(sim_time, msg))
