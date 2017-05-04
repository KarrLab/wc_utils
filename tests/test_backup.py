""" 
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-03
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils import backup
import os
import shutil
import six
import tempfile
import unittest

if six.PY3:
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard


class TestBackupManager(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test(self):
        env = EnvironmentVarGuard()

        if not os.getenv('CODE_SERVER_TOKEN'):
            with open('tests/fixtures/secret/CODE_SERVER_TOKEN', 'r') as file:
                env.set('CODE_SERVER_TOKEN', file.read().rstrip())

        content = 'this is a test'
        filename = os.path.join(self.tempdir, 'backup.test.txt')
        with open(filename, 'w') as file:
            file.write(content)

        manager = backup.BackupManager(filename, archive_filename='',
                                       archive_remote_filename='wc_utils.backup.test.txt')

        self.assertEqual(manager.archive_filename, filename + '.tar.gz')

        # create
        manager.create()
        self.assertTrue(os.path.isfile(manager.archive_filename))

        # upload
        manager.upload()

        # download
        manager.archive_filename = filename + '.2.tar.gz'
        manager.download()

        self.assertTrue(os.path.isfile(manager.archive_filename))

        # extract
        os.remove(filename)
        manager.extract()

        with open(filename, 'r') as file:
            self.assertEqual(file.read(), content)

        manager.cleanup()
