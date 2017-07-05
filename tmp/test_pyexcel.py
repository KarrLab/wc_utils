import unittest

import logging
import logging.config
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.config.fileConfig('log.conf')

import pyexcel

class TestPyexcel(unittest.TestCase):

    def test(self):
        data = [ [1, 3], [2, 4], ]
        pyexcel.save_as(array=data, dest_file_name='text.xlsx')
