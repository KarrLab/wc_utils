""" 
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-03
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils import backup
import copy
import ftputil
import mock
import os
import shutil
import six
import tempfile
import unittest
import wc_utils.util.git

if six.PY3:
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard


class TestBackupManager(unittest.TestCase):

    def setUp(self):
        self.tempdir_up = tempfile.mkdtemp()
        self.tempdir_down = tempfile.mkdtemp()

        env = EnvironmentVarGuard()

        if not os.getenv('CODE_SERVER_HOSTNAME'):
            with open('tests/fixtures/secret/CODE_SERVER_HOSTNAME', 'r') as file:
                env.set('CODE_SERVER_HOSTNAME', file.read().rstrip())

        if not os.getenv('CODE_SERVER_USERNAME'):
            with open('tests/fixtures/secret/CODE_SERVER_USERNAME', 'r') as file:
                env.set('CODE_SERVER_USERNAME', file.read().rstrip())

        if not os.getenv('CODE_SERVER_PASSWORD'):
            with open('tests/fixtures/secret/CODE_SERVER_PASSWORD', 'r') as file:
                env.set('CODE_SERVER_PASSWORD', file.read().rstrip())

        if not os.getenv('CODE_SERVER_REMOTE_DIRNAME'):
            with open('tests/fixtures/secret/CODE_SERVER_REMOTE_DIRNAME', 'r') as file:
                env.set('CODE_SERVER_REMOTE_DIRNAME', file.read().rstrip())

        self.manager = backup.BackupManager()

    def tearDown(self):
        shutil.rmtree(self.tempdir_up)
        shutil.rmtree(self.tempdir_down)

        manager = self.manager

        with ftputil.FTPHost(manager.hostname, manager.username, manager.password) as ftp:
            filename = ftp.path.join(manager.remote_dirname, 'test.wc_utils.backup.tar.gz')

            # remove directory for uploads
            if ftp.path.isdir(filename):
                ftp.rmtree(filename)

    def test(self):
        manager = self.manager

        # create
        content1 = 'this is a test 1'
        filename1 = os.path.join(self.tempdir_up, '1_a.txt')
        with open(filename1, 'w') as file:
            file.write(content1)

        content2 = 'this is a test 2'
        filename2 = os.path.join(self.tempdir_up, '2_a.txt')
        with open(filename2, 'w') as file:
            file.write(content2)

        os.mkdir(os.path.join(self.tempdir_up, 'dir_a'))
        content3 = 'this is a test 3'
        filename3 = os.path.join(self.tempdir_up, 'dir_a', '3_a.txt')
        with open(filename3, 'w') as file:
            file.write(content3)

        os.mkdir(os.path.join(self.tempdir_up, 'dir_a', 'subdir_a'))
        content4 = 'this is a test 4'
        filename4 = os.path.join(self.tempdir_up, 'dir_a', 'subdir_a', '4_a.txt')
        with open(filename4, 'w') as file:
            file.write(content4)

        paths_up = [
            backup.BackupPath(os.path.join(self.tempdir_up, '1_a.txt'), '1_b.txt'),
            backup.BackupPath(os.path.join(self.tempdir_up, '2_a.txt'), '2_b.txt'),
            backup.BackupPath(os.path.join(self.tempdir_up, 'dir_a'), 'dir_b'),
        ]
        a_backup_up = backup.Backup(paths=paths_up)
        a_backup_up.local_filename = os.path.join(self.tempdir_up, 'up.tar.gz')
        a_backup_up.remote_filename = 'test.wc_utils.backup.tar.gz'
        a_backup_up.set_username_ip_date()
        a_backup_up.set_package()

        manager.create(a_backup_up)
        self.assertTrue(os.path.isfile(a_backup_up.local_filename))

        # upload
        manager.upload(a_backup_up)

        # download
        paths_down = [
            backup.BackupPath(os.path.join(self.tempdir_down, '1_c.txt'), '1_b.txt'),
            backup.BackupPath(os.path.join(self.tempdir_down, '2_c.txt'), '2_b.txt'),
            backup.BackupPath(os.path.join(self.tempdir_down, 'dir_c'), 'dir_b'),
        ]
        a_backup_down = backup.Backup(paths=paths_down)
        a_backup_down.local_filename = os.path.join(self.tempdir_down, 'down.tar.gz')
        a_backup_down.remote_filename = a_backup_up.remote_filename

        manager.download(a_backup_down)
        self.assertTrue(os.path.isfile(a_backup_down.local_filename))

        # extract
        manager.extract(a_backup_down)

        with open(os.path.join(self.tempdir_down, '1_c.txt'), 'r') as file:
            self.assertEqual(file.read(), 'this is a test 1')

        with open(os.path.join(self.tempdir_down, '2_c.txt'), 'r') as file:
            self.assertEqual(file.read(), 'this is a test 2')

        with open(os.path.join(self.tempdir_down, 'dir_c', '3_a.txt'), 'r') as file:
            self.assertEqual(file.read(), 'this is a test 3')

        with open(os.path.join(self.tempdir_down, 'dir_c', 'subdir_a', '4_a.txt'), 'r') as file:
            self.assertEqual(file.read(), 'this is a test 4')

        self.assertEqual(a_backup_down.package, a_backup_up.package)
        self.assertEqual(a_backup_down.package_version, a_backup_up.package_version)
        self.assertEqual(a_backup_down.username, a_backup_up.username)
        self.assertEqual(a_backup_down.ip, a_backup_up.ip)
        self.assertEqual(a_backup_down.date, a_backup_up.date)

        manager.cleanup(a_backup_up)
        manager.cleanup(a_backup_down)
        self.assertFalse(os.path.isfile(a_backup_up.local_filename))
        self.assertFalse(os.path.isfile(a_backup_down.local_filename))
