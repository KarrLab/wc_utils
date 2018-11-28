""" Tests of Quilt Manager

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-08-07
:Copyright: 2018, Karr Lab
:License: MIT
"""

import capturer
import csv
import mock
import os
try:
    quilt_installed = True
    import quilt
    import quilt.tools.command
except:
    quilt_installed = False
import random
import shutil
import tempfile
import unittest
import wc_utils.config
import wc_utils.quilt
import wc_utils.workbook


@unittest.skipUnless(quilt_installed, 'Quilt must be installed')
class QuiltManagerTestCase(unittest.TestCase):

    def setUp(self):
        config = wc_utils.config.get_config()['wc_utils']['quilt']
        self.package = 'test__'
        self.owner = config['owner']
        self.owner_package = '{}/{}'.format(self.owner, self.package)
        self.token = config['token']
        self.tempdir_up = tempfile.mkdtemp()
        self.tempdir_down = tempfile.mkdtemp()
        self.delete_test_package_locally()
        self.delete_test_package_remotely()

    def tearDown(self):
        self.delete_test_package_locally()
        self.delete_test_package_remotely()
        shutil.rmtree(self.tempdir_up)
        shutil.rmtree(self.tempdir_down)

    def delete_test_package_locally(self):
        # remove local package
        with capturer.CaptureOutput(relay=False):
            quilt.rm('{}/{}'.format(self.owner, self.package), force=True)

    def delete_test_package_remotely(self):
        # delete package from Quilt server, if it exists
        try:
            with capturer.CaptureOutput(relay=False):
                quilt.login_with_token(self.token)
                quilt.access_list(self.owner_package)
                with mock.patch('quilt.tools.command.input', return_value=self.owner_package):
                    quilt.delete(self.owner_package)
        except quilt.tools.command.HTTPResponseException as err:
            if str(err) != 'Package {} does not exist'.format(self.owner_package):
                raise(err)

    def test_download_quilt_example(self):
        manager = wc_utils.quilt.QuiltManager(self.tempdir_down, 'iris', owner='uciml', token=self.token)
        manager.download()
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'README.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'iris_data.csv')))

    def test_gen_package_build_config(self):
        self.create_test_package()
        manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        actual = manager.gen_package_build_config()

        expected = {
            'contents': {
                'README': {
                    'file': 'README.md'
                },
                'binary': {
                    'test_binary_1': {
                        'file': 'binary/test_binary_1.bin',
                        'transform': 'id',
                    },
                    'test_binary_2': {
                        'file': 'binary/test_binary_2.bin',
                        'transform': 'id',
                    },
                },
                'csv': {
                    'subdir1': {
                        'subdir2': {
                            'test_csv_4': {
                                'file': 'csv/subdir1/subdir2/test_csv_4.csv',
                                'transform': 'csv',
                            },
                        },
                        'test_csv_3': {
                            'file': 'csv/subdir1/test_csv_3.csv',
                            'transform': 'csv',
                        },
                    },
                },
                'xlsx': {
                    'test_xlsx_5': {
                        'file': 'xlsx/test_xlsx_5.xlsx',
                        'transform': 'id',
                    },
                    'test_xlsx_6': {
                        'file': 'xlsx/test_xlsx_6.xlsx',
                        'transform': 'id',
                    },
                },
                'a_b_c': {
                    'd_e_f': {
                        'g_h_i_j_k': {
                            'file': 'a.b-c/d.e-f/g.h-i.j-k.l',
                            'transform': 'id',
                        }
                    }
                }
            },
        }

        self.assertEqual(actual, expected)

    def test_gen_package_build_config_error(self):
        self.create_test_package(empty=True)
        manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        with self.assertRaisesRegex(ValueError, 'Quilt does not support empty directories'):
            manager.gen_package_build_config()

    def test_upload(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        manager.upload()

        # check package created locally
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            quilt.ls()
            self.assertRegex(captured.stdout.get_text(), manager.get_owner_package())

        # check that package pushed to Quilt servers (i.e. no HTTPResponseException that package doesn't exist)
        with capturer.CaptureOutput(relay=False):
            quilt.login_with_token(self.token)
            quilt.access_list(manager.get_owner_package())

    def test_download(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        up_manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        up_manager.upload()

        down_manager = wc_utils.quilt.QuiltManager(self.tempdir_down, self.package, owner=self.owner, token=self.token)
        down_manager.download()

        self.assertTrue(os.path.isdir(os.path.join(self.tempdir_down, 'binary')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir_down, 'csv')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir_down, 'csv', 'subdir1')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'subdir2')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir_down, 'xlsx')))

        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'README.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'binary', 'test_binary_1.bin')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'binary', 'test_binary_2.bin')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'test_csv_3.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'subdir2', 'test_csv_4.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'xlsx', 'test_xlsx_5.xlsx')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir_down, 'xlsx', 'test_xlsx_6.xlsx')))

        with open(os.path.join(self.tempdir_down, 'README.md'), 'r') as file:
            self.assertEqual(file.readline(), '# Test package\n')
            self.assertEqual(file.readline(), 'Generated by `wc_utils/tests/test_quilt.py`\n')

        with open(os.path.join(self.tempdir_down, 'binary', 'test_binary_1.bin'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand1)
        with open(os.path.join(self.tempdir_down, 'binary', 'test_binary_2.bin'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand2)

        with open(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'test_csv_3.csv'), 'r') as file:
            self.assertEqual(file.readline(), 'X,Y\n')
            csv_reader = csv.reader(file)
            for i_row, row in enumerate(list(csv_reader)):
                self.assertEqual(int(row[0]), self.rand3[2 * i_row])
                self.assertEqual(int(row[1]), self.rand3[2 * i_row + 1])

        with open(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'subdir2', 'test_csv_4.csv'), 'r') as file:
            self.assertEqual(file.readline(), 'X,Y\n')
            csv_reader = csv.reader(file)
            for i_row, row in enumerate(csv_reader):
                self.assertEqual(int(row[0]), self.rand4[2 * i_row])
                self.assertEqual(int(row[1]), self.rand4[2 * i_row + 1])

        wb = wc_utils.workbook.io.ExcelReader(os.path.join(self.tempdir_down, 'xlsx', 'test_xlsx_5.xlsx')).run()
        ws = wb['Ws']
        self.assertEqual(ws[0][0], 'W')
        self.assertEqual(ws[0][1], 'X')
        self.assertEqual(ws[0][2], 'Y')
        self.assertEqual(ws[0][3], 'Z')
        for i_row, row in enumerate(ws[1:]):
            self.assertEqual(row[0], self.rand5[4 * i_row])
            self.assertEqual(row[1], self.rand5[4 * i_row + 1])
            self.assertEqual(row[2], self.rand5[4 * i_row + 2])
            self.assertEqual(row[3], self.rand5[4 * i_row + 3])

        wb = wc_utils.workbook.io.ExcelReader(os.path.join(self.tempdir_down, 'xlsx', 'test_xlsx_6.xlsx')).run()
        ws = wb['Ws']
        self.assertEqual(ws[0][0], 'W')
        self.assertEqual(ws[0][1], 'X')
        self.assertEqual(ws[0][2], 'Y')
        self.assertEqual(ws[0][3], 'Z')
        for i_row, row in enumerate(ws[1:]):
            self.assertEqual(row[0], self.rand6[4 * i_row])
            self.assertEqual(row[1], self.rand6[4 * i_row + 1])
            self.assertEqual(row[2], self.rand6[4 * i_row + 2])
            self.assertEqual(row[3], self.rand6[4 * i_row + 3])

        with open(os.path.join(self.tempdir_down, 'a.b-c', 'd.e-f', 'g.h-i.j-k.l'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand7)

    def test_download_single_file(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        up_manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        up_manager.upload()
        self.delete_test_package_locally()

        down_manager = wc_utils.quilt.QuiltManager(self.tempdir_down, self.package, owner=self.owner, token=self.token)
        down_manager.download(system_path='binary/test_binary_1.bin')

        with open(os.path.join(self.tempdir_down, 'binary', 'test_binary_1.bin'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand1)
        self.assertFalse(os.path.isfile(os.path.join(self.tempdir_down, 'binary', 'test_binary_2.bin')))
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'csv')))
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'xlsx')))

        down_manager.download(system_path='a.b-c/d.e-f/g.h-i.j-k.l')
        with open(os.path.join(self.tempdir_down, 'a.b-c', 'd.e-f', 'g.h-i.j-k.l'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand7)

        with self.assertRaisesRegex(ValueError, 'does not contain'):
            down_manager.download(system_path='binary/non_existent.bin')

    def test_download_single_file_sym_links(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        up_manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        up_manager.upload()
        self.delete_test_package_locally()

        down_manager = wc_utils.quilt.QuiltManager(self.tempdir_down, self.package, owner=self.owner, token=self.token)
        down_manager.download(system_path='binary/test_binary_1.bin', sym_links=True)

        with open(os.path.join(self.tempdir_down, 'binary', 'test_binary_1.bin'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand1)
        self.assertFalse(os.path.isfile(os.path.join(self.tempdir_down, 'binary', 'test_binary_2.bin')))
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'csv')))
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'xlsx')))

    def test_download_single_dir(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        up_manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        up_manager.upload()
        self.delete_test_package_locally()

        down_manager = wc_utils.quilt.QuiltManager(self.tempdir_down, self.package, owner=self.owner, token=self.token)
        down_manager.download(system_path='binary/')

        with open(os.path.join(self.tempdir_down, 'binary', 'test_binary_1.bin'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand1)
        with open(os.path.join(self.tempdir_down, 'binary', 'test_binary_2.bin'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand2)
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'csv')))
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'xlsx')))

        down_manager.download(system_path='a.b-c/d.e-f')
        with open(os.path.join(self.tempdir_down, 'a.b-c', 'd.e-f', 'g.h-i.j-k.l'), 'rb') as file:
            self.assertEqual([int(b) for b in file.read()], self.rand7)

        with self.assertRaisesRegex(ValueError, 'does not contain'):
            down_manager.download(system_path='binary/non_existent.bin')

    def test_download_single_dir_2(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        up_manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        up_manager.upload()
        self.delete_test_package_locally()

        down_manager = wc_utils.quilt.QuiltManager(self.tempdir_down, self.package, owner=self.owner, token=self.token)
        down_manager.download(system_path='csv')

        with open(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'test_csv_3.csv'), 'r') as file:
            self.assertEqual(file.readline(), 'X,Y\n')
            csv_reader = csv.reader(file)
            for i_row, row in enumerate(list(csv_reader)):
                self.assertEqual(int(row[0]), self.rand3[2 * i_row])
                self.assertEqual(int(row[1]), self.rand3[2 * i_row + 1])

        with open(os.path.join(self.tempdir_down, 'csv', 'subdir1', 'subdir2', 'test_csv_4.csv'), 'r') as file:
            self.assertEqual(file.readline(), 'X,Y\n')
            csv_reader = csv.reader(file)
            for i_row, row in enumerate(csv_reader):
                self.assertEqual(int(row[0]), self.rand4[2 * i_row])
                self.assertEqual(int(row[1]), self.rand4[2 * i_row + 1])

        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'binary')))
        self.assertFalse(os.path.isdir(os.path.join(self.tempdir_down, 'xlsx')))

        with self.assertRaisesRegex(ValueError, 'does not contain'):
            down_manager.download(system_path='csv/non_existent.csv')

    def test_get_package_path(self):
        # create files for test package
        self.create_test_package()

        # build Quilt package and push to servers
        up_manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package, owner=self.owner, token=self.token)
        up_manager.upload()

        down_manager = wc_utils.quilt.QuiltManager(self.tempdir_down, self.package, owner=self.owner, token=self.token)
        self.assertEqual(down_manager.get_package_path('binary/test_binary_1.bin'),
                         'binary/test_binary_1')
        self.assertEqual(down_manager.get_package_path('binary/test_binary_2.bin'),
                         'binary/test_binary_2')
        self.assertEqual(down_manager.get_package_path('csv/subdir1/test_csv_3.csv'),
                         'csv/subdir1/test_csv_3')
        self.assertEqual(down_manager.get_package_path('csv/subdir1/subdir2/test_csv_4.csv'),
                         'csv/subdir1/subdir2/test_csv_4')
        self.assertEqual(down_manager.get_package_path('non_existent'),
                         None)

        self.assertEqual(down_manager.get_package_path('binary'),
                         'binary')
        self.assertEqual(down_manager.get_package_path('binary/'),
                         'binary')
        self.assertEqual(down_manager.get_package_path('csv/subdir1'),
                         'csv/subdir1')
        self.assertEqual(down_manager.get_package_path('csv/subdir1/'),
                         'csv/subdir1')
        self.assertEqual(down_manager.get_package_path('csv/subdir1/subdir2'),
                         'csv/subdir1/subdir2')
        self.assertEqual(down_manager.get_package_path('csv/subdir1/subdir2/'),
                         'csv/subdir1/subdir2')
        self.assertEqual(down_manager.get_package_path('non_existent/subdir'),
                         None)

    def create_test_package(self, empty=False):
        # create files for test package
        # - binary
        # - CSV
        # - XSLX
        with open(os.path.join(self.tempdir_up, 'README.md'), 'w') as file:
            file.write('# Test package\n')
            file.write('Generated by `wc_utils/tests/test_quilt.py`\n')

        os.mkdir(os.path.join(self.tempdir_up, 'binary'))
        os.mkdir(os.path.join(self.tempdir_up, 'csv'))
        os.mkdir(os.path.join(self.tempdir_up, 'csv', 'subdir1'))
        os.mkdir(os.path.join(self.tempdir_up, 'csv', 'subdir1', 'subdir2'))
        os.mkdir(os.path.join(self.tempdir_up, 'xlsx'))
        os.mkdir(os.path.join(self.tempdir_up, 'a.b-c'))
        os.mkdir(os.path.join(self.tempdir_up, 'a.b-c', 'd.e-f'))
        if empty:
            os.mkdir(os.path.join(self.tempdir_up, 'empty'))
            os.mkdir(os.path.join(self.tempdir_up, 'empty', 'subdir3'))
            os.mkdir(os.path.join(self.tempdir_up, 'empty', 'subdir3', 'subdir4'))

        self.rand1 = rand1 = [random.randint(0, 255) for i in range(1000)]
        self.rand2 = rand2 = [random.randint(0, 255) for i in range(1000)]
        with open(os.path.join(self.tempdir_up, 'binary', 'test_binary_1.bin'), 'wb') as file:
            file.write(bytes(rand1))
        with open(os.path.join(self.tempdir_up, 'binary', 'test_binary_2.bin'), 'wb') as file:
            file.write(bytes(rand2))

        self.rand3 = rand3 = [random.randint(0, 255) for i in range(1000)]
        self.rand4 = rand4 = [random.randint(0, 255) for i in range(1000)]
        with open(os.path.join(self.tempdir_up, 'csv', 'subdir1', 'test_csv_3.csv'), 'w') as file:
            file.write('X,Y\n')
            for i in range(0, 1000, 2):
                file.write('{},{}\n'.format(rand3[i], rand3[i+1]))
        with open(os.path.join(self.tempdir_up, 'csv', 'subdir1', 'subdir2', 'test_csv_4.csv'), 'w') as file:
            file.write('X,Y\n')
            for i in range(0, 1000, 2):
                file.write('{},{}\n'.format(rand4[i], rand4[i+1]))

        self.rand5 = rand5 = [random.randint(0, 255) for i in range(1000)]
        self.rand6 = rand6 = [random.randint(0, 255) for i in range(1000)]
        wb = wc_utils.workbook.Workbook()
        ws = wb['Ws'] = wc_utils.workbook.Worksheet()
        ws.append(wc_utils.workbook.Row(['W', 'X', 'Y', 'Z']))
        for i in range(0, 1000, 4):
            ws.append(wc_utils.workbook.Row(rand5[i:i+4]))
        wc_utils.workbook.io.ExcelWriter(os.path.join(self.tempdir_up, 'xlsx', 'test_xlsx_5.xlsx')).run(wb)

        wb = wc_utils.workbook.Workbook()
        ws = wb['Ws'] = wc_utils.workbook.Worksheet()
        ws.append(wc_utils.workbook.Row(['W', 'X', 'Y', 'Z']))
        for i in range(0, 1000, 4):
            ws.append(wc_utils.workbook.Row(rand6[i:i+4]))
        wc_utils.workbook.io.ExcelWriter(os.path.join(self.tempdir_up, 'xlsx', 'test_xlsx_6.xlsx')).run(wb)

        self.rand7 = rand7 = [random.randint(0, 255) for i in range(1000)]
        with open(os.path.join(self.tempdir_up, 'a.b-c', 'd.e-f', 'g.h-i.j-k.l'), 'wb') as file:
            file.write(bytes(rand7))

    def test_get_owner_package(self):
        manager = wc_utils.quilt.QuiltManager(self.tempdir_up, 'package-id', owner='owner-id')
        self.assertEqual(manager.get_owner_package(), 'owner-id/package-id')

    @unittest.skipUnless(wc_utils.config.get_config()['wc_utils']['quilt']['username'] and
                         wc_utils.config.get_config()['wc_utils']['quilt']['password'],
                         'Quilt username and password required for test')
    def test_get_token(self):
        manager = wc_utils.quilt.QuiltManager(self.tempdir_up, self.package)
        token = manager.get_token()
        self.assertEqual(len(token), 225)
