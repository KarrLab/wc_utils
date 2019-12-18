""" High-level interface for the Quilt data revisioning system

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2019-10-08
:Copyright: 2018-2019, Karr Lab
:License: MIT
"""

from wc_utils.config import get_config
import boto3
import datetime
import json
import os
import requests
import quilt3


class QuiltManager(object):
    """ Manager for Quilt packages

    Quilt credentials and configuration can be stored in a `wc_utils` configuration file
    (e.g., `~/.wc/wc_utils.cfg`) or passed to the constructor::

        [wc_utils]
            [[quilt]]
                username = ...
                password = ...
                aws_bucket = ...
                aws_profile = ...

    AWS S3 credentials should be stored in `~/.aws/credentials`::

        [default]
        aws_access_key_id = ...
        aws_secret_access_key = ...

    AWS S3 regions should be configured in `~/.aws/config`::

        [default]
        region=us-east-1
        output=json

    Attributes:
        path (:obj:`str`): local path to package
        namespace (:obj:`str`): namespace for package
        package (:obj:`str`): name of package
        hash (:obj:`str`): hash of version of package
        registry (:obj:`str`): URL for Quilt registry
        username (:obj:`str`): Quilt user name
        password (:obj:`str`): Quilt password
        aws_bucket (:obj:`str`): AWS bucket to store/access packages
        aws_profile (:obj:`str`): AWS profile (credentials) to
            store/access packages
    """

    def __init__(self, path=None, namespace=None, package=None, hash=None,
                 registry=None, username=None, password=None,
                 aws_bucket=None, aws_profile=None):
        """
        Args:
            path (:obj:`str`): local path to package
            namespace (:obj:`str`, optional): namespace for package
            package (:obj:`str`): name of package
            hash (:obj:`str`, optional): hash of version of package
            registry (:obj:`str`, optional): URL for Quilt registry
            username (:obj:`str`, optional): user name
            password (:obj:`str`, optional): password
            aws_bucket (:obj:`str`, optional): AWS bucket to store/access packages
            aws_profile (:obj:`str`, optional): AWS profile (credentials) to
                store/access packages
        """
        config = get_config()['wc_utils']['quilt']
        self.path = path
        self.namespace = namespace or config['namespace']
        self.package = package
        self.hash = hash
        self.registry = registry or config['registry']
        self.username = username or config['username']
        self.password = password or config['password']
        self.aws_bucket = aws_bucket or config['aws_bucket']
        self.aws_profile = aws_profile or config['aws_profile']

        self.config()
        self.login()

    def config(self):
        """ Configure the Quilt client to the desired AWS S3 bucket
        ("remote Quilt registry")
        """
        quilt3.config(self.registry)
        quilt3.config(default_remote_registry=self.get_aws_bucket_uri())

    def login(self, credentials='aws'):
        """ Login with user or session token """
        if credentials == 'quilt':
            self._login_via_quilt()
        elif credentials == 'aws':
            self._login_via_aws()
        else:
            raise ValueError('Login must be via "quilt" or "aws"')

    def _login_via_quilt(self):
        """ Login with user or session token """
        user_token = self._get_user_token()
        session_token = self._get_session_token(user_token)
        quilt3.session.login_with_token(session_token)

    def _login_via_aws(self):
        """ Login with AWS credentials """
        session = boto3.Session(profile_name=self.aws_profile)
        credentials = session.get_credentials()
        now = datetime.datetime.now() + datetime.timedelta(0, 3600 * 12)
        s3_credentials = {
            'access_key': credentials.access_key,
            'secret_key': credentials.secret_key,
            'token': None,
            'expiry_time': now.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
        }
        with open(quilt3.session.CREDENTIALS_PATH, 'w') as file:
            json.dump(s3_credentials, file)

        quilt3.session.AUTH_PATH.touch()

    def _get_user_token(self):
        """ Get a token for a user

        Returns:
            :obj:`str`: token for the user

        Raises:
            :obj:`AssertionError`: if unable to login into Quilt
        """
        response = requests.post(self.registry + '/api/login',
                                 json={
                                     'username': self.username,
                                     'password': self.password,
                                 })
        response.raise_for_status()
        json = response.json()
        assert json['status'] == 200, 'Unable to log into Quilt'
        return json['token']

    def _get_session_token(self, user_token):
        """ Get a token for a session

        Args:
            user_token (:obj:`str`): user token obtain with :obj:`get_user_token`

        Returns:
            :obj:`str`: token for a session

        Raises:
            :obj:`AssertionError`: if unable to get a token for a session
        """
        response = requests.get(self.registry + '/api/code',
                                headers={
                                    'Authorization': 'Bearer ' + user_token,
                                })
        response.raise_for_status()
        json = response.json()
        assert json['status'] == 200, 'Unable to get token for Quilt session'
        return json['code']

    def _get_aws_token(self, user_token):
        """ Get a token for a session

        Args:
            user_token (:obj:`str`): user token obtain with :obj:`get_user_token`

        Returns:
            :obj:`dict`: dictionary with AWS access and secret keys

        Raises:
            :obj:`AssertionError`: if unable to get a token for a session
        """
        response = requests.get(self.registry + '/api/auth/get_credentials',
                                headers={
                                    'Authorization': 'Bearer ' + user_token,
                                })
        response.raise_for_status()
        json = response.json()
        assert json['status'] == 200, 'Unable to get keys for Quilt session'
        return {
            'access_key': json['AccessKeyId'],
            'secret_key': json['SecretAccessKey'],
            'session_token': json['SessionToken'],
            'expiry_time': json['Expiration'],
        }

    def upload_package(self, message=None):
        """ Build and upload package from local directory,
        ignoring all files listed in .quiltignore

        Args:
            message (:obj:`str`): commit message
        """

        # build package, ignoring all files in .quiltignore
        package = quilt3.Package()
        package.set_dir('/', self.path)

        # upload package
        package.push(self.get_full_package_id(), message=message)

    def download_package(self, path=None):
        """ Download package, or a path within a package, to local directory

        Args:
            path (:obj:`str`, optional): path within a package to download
        """
        if path:
            # download a path within a package
            package = quilt3.Package.browse(self.get_full_package_id(), top_hash=self.hash,
                                            registry=self.get_aws_bucket_uri())
            package[path].fetch(dest=os.path.join(self.path, path))

        else:
            # download full package
            quilt3.Package.install(self.get_full_package_id(), top_hash=self.hash, dest=self.path)

    def get_packages(self):
        """ Get the names of the packages in the S3 bucket

        Returns:
            :obj:`list` of :obj:`str`: list of package names
        """
        packages = quilt3.list_packages(self.get_aws_bucket_uri())
        return list(packages)

    def delete_package(self, del_from_bucket=True):
        """ Delete package

        Args:
            del_from_bucket (:obj:`bool`, optional): if :obj:`True`, delete the
                files for the package from the AWS bucket
        """
        quilt3.delete_package(self.get_full_package_id(), registry=self.get_aws_bucket_uri())

        if del_from_bucket:
            bucket = quilt3.Bucket(self.get_aws_bucket_uri())
            bucket.delete_dir('.quilt/named_packages/' + self.get_full_package_id() + '/')
            bucket.delete_dir(self.get_full_package_id() + '/')

    def get_full_package_id(self):
        """ Get the full id of a package (namespace and package id)

        Returns:
            :obj:`str`: full package id
        """
        return self.namespace + '/' + self.package

    def get_aws_bucket_uri(self):
        """ Get the full URI of an AWS S3 bucket (s3:// + bucket id)

        Returns:
            :obj:`str`: full URI of an AWS S3 bucket
        """
        return 's3://' + self.aws_bucket

    def upload_file_to_bucket(self, path, key):
        """ Upload file to AWS S3 bucket

        Args:
            path (:obj:`str`): path to file to upload
            key (:obj:`str`): path within bucket to save file
        """
        bucket = quilt3.Bucket(self.get_aws_bucket_uri())
        bucket.put_file(key, path)

    def download_file_from_bucket(self, key, path):
        """ Get file from AWS S3 bucket

        Args:
            key (:obj:`str`): path within bucket to file
            path (:obj:`str`): path to save file
        """
        bucket = quilt3.Bucket(self.get_aws_bucket_uri())
        bucket.fetch(key, path)

    def delete_file_from_bucket(self, key):
        """ Delete file to AWS S3 bucket

        Args:
            key (:obj:`str`): path within bucket to save file
        """
        bucket = quilt3.Bucket(self.get_aws_bucket_uri())
        bucket.delete(key)
