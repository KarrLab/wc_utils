""" 
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-03-12
:Copyright: 2018, Karr Lab
:License: MIT
"""

import types
import unittest
import wc_utils


class ApiTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(wc_utils.backup, types.ModuleType)
        self.assertIsInstance(wc_utils.backup.BackupManager, type)
