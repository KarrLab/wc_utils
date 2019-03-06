""" Tests of the file utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-11
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_utils.util import files
import os
import shutil
import tempfile
import unittest
import getpass
from pathlib import Path


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

        #src and dest are files
        files.copytree_to_existing_destination(os.path.join(base, 'a', 'b', 'c'), os.path.join(base, 'D'))
        with open(os.path.join(base, 'D'), 'r') as file:
            self.assertEqual(file.read(), '3')

    def test_normalize_filename(self):
        normalize_filename = files.normalize_filename

        self.assertEqual(normalize_filename('~'), normalize_filename('~' + getpass.getuser()))
        self.assertEqual(normalize_filename('~'), normalize_filename('$HOME'))
        cur_dir = os.path.dirname(__file__)
        self.assertEqual(cur_dir,
            normalize_filename(os.path.join(cur_dir, '..', os.path.basename(cur_dir))))
        test_filename = os.path.join(cur_dir, 'test_filename')
        self.assertEqual(test_filename, normalize_filename('test_filename', dir=os.path.dirname(test_filename)))
        self.assertEqual(os.path.join(os.getcwd(), 'test_filename'), normalize_filename('test_filename'))
        with self.assertRaisesRegex(ValueError, r"directory '.+' isn't absolute"):
            normalize_filename('test_filename', dir='~')

    def test_normalize_filenames(self):
        tmp_path = os.path.join(self.dirname, 'foo')
        self.assertEqual(files.normalize_filenames([tmp_path]), [tmp_path])
        file_in_dir = os.path.join('dir_name', 'bar')
        expected_abs_file_in_dir = os.path.join(self.dirname, file_in_dir)
        self.assertEqual(files.normalize_filenames([tmp_path, file_in_dir], absolute_file=tmp_path),
            [tmp_path, expected_abs_file_in_dir])

    def test_remove_silently(self):
        test_file = os.path.join(self.dirname, 'test_file')
        Path(test_file).touch()
        self.assertEqual(files.remove_silently(test_file), None)

        no_such_file = os.path.join(self.dirname, 'no_such_file')
        self.assertEqual(files.remove_silently(no_such_file), None)

        with self.assertRaises(TypeError):
            files.remove_silently(12)