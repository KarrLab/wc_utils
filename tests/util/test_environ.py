""" Test EnvironUtils

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-10-24
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from wc_utils.util.environ import EnvironUtils
import os
import unittest


class TestEnvironUtils(unittest.TestCase):

    def test_mktemp(self):
        path = os.getenv('PATH')
        self.assertNotEqual(path, 'test')

        with EnvironUtils.make_temp_environ(PATH='test'):
            self.assertEqual(os.getenv('PATH'), 'test')

        self.assertEqual(os.getenv('PATH'), path)
