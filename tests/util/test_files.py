""" Tests of the file utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-05-11
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_utils.util import files
import os
import shutil
import tempfile
import unittest


class FileUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_copytree_to_existing_destination(self):
        base = self.dirname

        os.mkdir(os.path.join(base, 'a'))
        os.mkdir(os.path.join(base, 'a', 'b'))
        with open(os.path.join(base, 'a', 'b', 'c'), 'w') as file:
            file.write('3')
        with open(os.path.join(base, 'a', 'b', 'd'), 'w') as file:
            file.write('4')

        # destination doesn't exist
        files.copytree_to_existing_destination(os.path.join(base, 'a'), os.path.join(base, 'A'))
        with open(os.path.join(base, 'A', 'b', 'c'), 'r') as file:
            self.assertEqual(file.read(), '3')

        # destination exists, but empty
        os.mkdir(os.path.join(base, 'B'))
        files.copytree_to_existing_destination(os.path.join(base, 'a'), os.path.join(base, 'B'))
        with open(os.path.join(base, 'B', 'b', 'c'), 'r') as file:
            self.assertEqual(file.read(), '3')

        # destination exists, but not empty
        os.mkdir(os.path.join(base, 'C'))
        os.mkdir(os.path.join(base, 'C', 'b'))
        with open(os.path.join(base, 'C', 'b', 'c'), 'w') as file:
            file.write('4')
        with open(os.path.join(base, 'C', 'b', 'e'), 'w') as file:
            file.write('5')
        files.copytree_to_existing_destination(os.path.join(base, 'a'), os.path.join(base, 'C'))
        with open(os.path.join(base, 'C', 'b', 'c'), 'r') as file:
            self.assertEqual(file.read(), '3')
        with open(os.path.join(base, 'C', 'b', 'd'), 'r') as file:
            self.assertEqual(file.read(), '4')
        with open(os.path.join(base, 'C', 'b', 'e'), 'r') as file:
            self.assertEqual(file.read(), '5')
