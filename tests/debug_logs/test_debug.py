""" Info/debugging log tests

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-20
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utilities.debug_logs.debug import MakeLoggers
import io
import os
import sys
import tempfile
import unittest

from tests.config_files import config_constants
from wc_utilities.debug_logs.config_from_files_and_env import ConfigFromFilesAndEnv
from wc_utilities.debug_logs.debug import MakeLoggers
log_config = ConfigFromFilesAndEnv.setup( config_constants )
loggers = MakeLoggers().setup_logger( log_config )

def atts(obj):
    for a in dir(obj):
        if 'format' in a:
            print( a, getattr(obj, a) )
         
class DefaultDebugLogsTest(unittest.TestCase):

    def test_file(self):
        logger = loggers.get_logger('wc.debug.file')
        
        print('\nattributes of', 'wc.debug.file', 'logger' )
        atts(logger)

        handler = next(iter(logger.handlers))
        filename = handler.fh.name

        prev_size = os.path.getsize(filename)


        msg = 'debug message'
        logger.debug(msg)

        with open(filename, 'r') as file:
            file.seek(prev_size)
            new_log = file.read()

        print('MSG:', new_log)
        self.assertRegexpMatches(new_log, '^.+?; .+?; .+?:.+?:\d+; {:f}; {:s}\n$'.format(
            float('nan'), msg))

    # @unittest.skip("skip, as not a test")
    def test_console(self):
        # TODO: make this a test
        logger = loggers.get_logger('wc.debug.console')

        msg = 'debug message'
        logger.debug(msg)

'''
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
                    'template': '{timestamp}; {name:s}; {level:s}; {src:s}:{func:s}:{line:d}; {sim_time:f}; {message:s}',
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
        loggers = debug_log.setup(debug_config)

        # get logger
        logger = debug_log.get_logger('__test__.file', loggers)

        # send message
        msg = 'debug message'
        logger.debug(msg)

        # assert log file created
        self.assertTrue(os.path.isfile(self._temp_log_file))

        # assert message saved to file
        with open(self._temp_log_file, 'r') as file:
            log = file.read()
        self.assertRegexpMatches(log, '^.+?; .+?; .+?:.+?:\d+; \d.\d+; {:s}\n$'.format(msg))


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
        loggers = debug_log.setup(debug_config)

        # get console logger
        logger = debug_log.get_logger('__test__.stream', loggers)

        # override stream
        next(iter(logger.handlers)).stream = self.stream

        # output message
        msg = 'debug message'
        sim_time = 2.5
        logger.debug(msg, sim_time=sim_time)

        # check message is correct
        self.assertRegexpMatches(self.stream.getvalue(), '^.+?; .+?; .+?:.+?:\d+; {:f}; {:s}\n$'.format(sim_time, msg))

'''
