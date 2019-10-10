""" Tests of the high-level interface for the Quilt data revisioning system

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2019-10-08
:Copyright: 2018-2019, Karr Lab
:License: MIT
"""

import boto3
import botocore.exceptions
import collections
import csv
import os
import quilt3
import shutil
import tempfile
import wc_utils.config
import wc_utils.quilt
import unittest


class S3TestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_access(self):
        config = wc_utils.config.get_config()['wc_utils']['quilt']

        datas = [
            collections.OrderedDict([('a', '1'), ('b', '2'), ('c', '3')]),
            collections.OrderedDict([('a', '4'), ('b', '5'), ('c', '6')]),
            collections.OrderedDict([('a', '7'), ('b', '8'), ('c', '9')]),
        ]
        filename = os.path.join(self.dirname, 'test.csv')
        with open(filename, 'w') as file:
            writer = csv.DictWriter(file, fieldnames=datas[0].keys())
            writer.writeheader()
            for data in datas:
                writer.writerow(data)

        key = 'test_quilt/test.csv'
        session = boto3.Session(profile_name=config['aws_profile'])
        s3 = session.resource('s3')
        bucket = s3.Bucket(config['aws_bucket'])

        with open(filename, 'rb') as file:
            bucket.put_object(Key=key, Body=file)

        filename2 = os.path.join(self.dirname, 'test2.csv')
        bucket.download_file(key, filename2)

        with open(filename2, 'r') as file:
            reader = csv.DictReader(file)
            datas2 = list(reader)

        for data2, data in zip(datas2, datas):
            self.assertEqual(data2, data)

        self.assertEqual(len(list(bucket.objects.filter(Prefix=key))), 1)
        self.assertEqual(list(bucket.objects.filter(Prefix=key))[0].key, key)

        bucket.delete_objects(Delete={'Objects': [{'Key': key}]})

        self.assertEqual(list(bucket.objects.filter(Prefix=key)), [])


class QuiltTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_config(self):
        mgr = wc_utils.quilt.QuiltManager()
        mgr.config()

    def test_login(self):
        mgr = wc_utils.quilt.QuiltManager()
        mgr.config()

        os.remove(quilt3.session.AUTH_PATH)
        os.remove(quilt3.session.CREDENTIALS_PATH)
        mgr.login(credentials='quilt')
        self.assertTrue(os.path.isfile(quilt3.session.AUTH_PATH))
        self.assertTrue(os.path.isfile(quilt3.session.CREDENTIALS_PATH))

        user_token = mgr._get_user_token()
        aws_token = mgr._get_aws_token(user_token)
        self.assertIn('access_key', aws_token)

        os.remove(quilt3.session.AUTH_PATH)
        os.remove(quilt3.session.CREDENTIALS_PATH)
        mgr.login(credentials='aws')
        self.assertTrue(os.path.isfile(quilt3.session.AUTH_PATH))
        self.assertTrue(os.path.isfile(quilt3.session.CREDENTIALS_PATH))

        with self.assertRaisesRegex(ValueError, 'Login must be via'):
            mgr.login(credentials=None)

    def test_upload_download_delete(self):
        up_dir = os.path.join(self.dirname, 'up')
        down_dir = os.path.join(self.dirname, 'down')
        down_dir2 = os.path.join(self.dirname, 'down2')

        os.mkdir(up_dir)
        with open(os.path.join(up_dir, '123.csv'), 'w') as file:
            file.write('1,2,3\n')
        os.mkdir(os.path.join(up_dir, 'abc'))
        with open(os.path.join(up_dir, 'abc', '456.csv'), 'w') as file:
            file.write('4,5,6\n')

        # login
        mgr = wc_utils.quilt.QuiltManager(path=up_dir, package='_test_')
        mgr.config()
        mgr.login()

        # if necessary, remove test package (i.e. cleanup from previously failed test)
        try:
            quilt3.Package.browse(mgr.get_full_package_id(), registry=mgr.get_aws_bucket_uri())
            mgr.delete_package()
        except botocore.exceptions.ClientError:
            pass

        # upload
        mgr.upload_package()
        quilt3.Package.browse(mgr.get_full_package_id(), registry=mgr.get_aws_bucket_uri())

        # download full package
        mgr.path = down_dir
        mgr.download_package()

        with open(os.path.join(down_dir, '123.csv'), 'r') as file:
            self.assertEqual(file.read(), '1,2,3\n')
        with open(os.path.join(down_dir, 'abc', '456.csv'), 'r') as file:
            self.assertEqual(file.read(), '4,5,6\n')

        # download part of package
        mgr.path = down_dir2
        mgr.download_package(path='abc')

        with open(os.path.join(down_dir2, 'abc', '456.csv'), 'r') as file:
            self.assertEqual(file.read(), '4,5,6\n')

        # delete
        mgr.delete_package()
        with self.assertRaises(botocore.exceptions.ClientError):
            quilt3.Package.browse(mgr.get_full_package_id(), registry=mgr.get_aws_bucket_uri())

    def test_get_packages(self):
        mgr = wc_utils.quilt.QuiltManager()

        mgr.config()
        mgr.login()
        packages = mgr.get_packages()
        self.assertIsInstance(packages, list)
        self.assertIn(mgr.namespace + '/' + 'datanator', packages)

    def test_upload_download_delete_file(self):
        mgr = wc_utils.quilt.QuiltManager()

        mgr.config()
        mgr.login()

        filename = os.path.join(self.dirname, 'test.md')
        filename2 = os.path.join(self.dirname, 'test2.md')
        with open(filename, 'w') as file:
            file.write('test me')

        key = '__test__'
        mgr.upload_file_to_bucket(filename, key)

        mgr.download_file_from_bucket(key, filename2)
        with open(filename2, 'r') as file:
            self.assertEqual(file.read(), 'test me')

        mgr.delete_file_from_bucket(key)
        config = wc_utils.config.get_config()['wc_utils']['quilt']
        session = boto3.Session(profile_name=config['aws_profile'])
        s3 = session.resource('s3')
        bucket = s3.Bucket(config['aws_bucket'])
        self.assertEqual(list(bucket.objects.filter(Prefix=key)), [])
