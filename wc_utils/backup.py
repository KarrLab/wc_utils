"""
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-03
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

import datetime
import dateutil.parser
import ftputil
import getpass
import io
import json
import os
import requests
import shutil
import six
import socket
import tarfile
import tempfile
import wc_utils.config.core
import wc_utils.util.git


class BackupManager(object):
    """ Manages backups of files to the Karr Lab code server

    Attributes:
        hostname (:obj:`str`): hostname for server to upload/download backups
        remote_dirname (:obj:`str`): remote directory on server to upload/download backups
        username (:obj:`str`): username for server to upload/download backups
        password (:obj:`str`): password for server to upload/download backups
    """

    def __init__(self, hostname=None, remote_dirname=None, username=None, password=None):
        """
        Args:
            hostname (:obj:`str`, optional): hostname for server to upload/download backups
            remote_dirname (:obj:`str`, optional): remote directory on server to upload/download backups
            username (:obj:`str`, optional): username for server to upload/download backups
            password (:obj:`str`, optional): password for server to upload/download backups
        """
        config = wc_utils.config.core.get_config()['wc_utils']['backup']
        self.hostname = hostname or config['hostname']
        self.remote_dirname = remote_dirname or config['remote_dirname']
        self.username = username or config['username']
        self.password = password or config['password']

    def create(self, backup):
        """ Create a gzip archive of a backup

        Args:
            backup (:obj:`Backup`): a backup

        Returns:
            :obj:`BackupManager`: backup manager
        """
        with tarfile.open(backup.local_filename, "w:gz") as tar:
            # add metadata to archive
            _, temp_filename = tempfile.mkstemp()
            with open(temp_filename, 'w') as temp_file:
                json.dump({
                    'package': backup.package,
                    'package_version': backup.package_version,
                    'username': backup.username,
                    'ip': backup.ip,
                    'date': backup.date.isoformat(),
                }, temp_file)
            tar.add(temp_filename, arcname='__metadata__.json')

            # add paths to archive
            for path in backup.paths:
                tar.add(path.path, arcname=path.arc_path)

        os.remove(temp_filename)

        return self

    def extract(self, backup):
        """ Extract a backup

        Args:
            backup (:obj:`Backup`): a backup

        Returns:
            :obj:`BackupManager`: backup manager
        """
        # extract archive
        with tarfile.open(backup.local_filename, "r:gz") as tar:
            tempdir = tempfile.mkdtemp()
            tar.extractall(tempdir)

        # read metadata
        if os.path.isfile(os.path.join(tempdir, '__metadata__.json')):
            with open(os.path.join(tempdir, '__metadata__.json'), 'r') as json_file:
                md = json.load(json_file)
                backup.package = md['package']
                backup.package_version = md['package_version']
                backup.username = md['username']
                backup.ip = md['ip']
                backup.date = dateutil.parser.parse(md['date'])

        # move files
        for path in backup.paths:
            shutil.move(os.path.join(tempdir, path.arc_path), path.path)

        # cleanup
        shutil.rmtree(tempdir)

        return self

    def upload(self, backup):
        """ Upload a backup to a server

        Args:
            backup (:obj:`Backup`): backup to upload

        Returns:
            :obj:`BackupManager`: the backup manager
        """

        with ftputil.FTPHost(self.hostname, self.username, self.password) as ftp:
            dirname = ftp.path.join(self.remote_dirname, backup.remote_filename)

            # create directory for uploads
            if not ftp.path.isdir(dirname):
                ftp.mkdir(dirname)

            # determine version number
            version = len(ftp.listdir(dirname))

            # upload file
            ftp.upload(backup.local_filename, ftp.path.join(dirname, str(version)))

        return self

    def download(self, backup, version=None):
        """ Download a backup from the server

        Args:
            backup (:obj:`Backup`): backup to download
            version (:obj:`int`, optional): version to download; if :obj:`None`, download the latest version

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        with ftputil.FTPHost(self.hostname, self.username, self.password) as ftp:
            dirname = ftp.path.join(self.remote_dirname, backup.remote_filename)

            # determine version number
            if version is None:
                version = len(ftp.listdir(dirname)) - 1

            # upload file
            ftp.download(ftp.path.join(dirname, str(version)), backup.local_filename)

        return self

    def cleanup(self, backup):
        """ Remove the archive

        Args:
            backup (:obj:`Backup`): backup to clean up

        Returns:
            :obj:`BackupManager`: backup manager
        """
        if os.path.isfile(backup.local_filename):
            os.remove(backup.local_filename)
        return self


class Backup(object):
    """ A list of paths to backup and metadata about the backup

    Attributes:
        local_filename (:obj:`str`): path to store the backup
        remote_filename (:obj:`str`): remote name of backup
        paths (obj:`list` of :obj:`BackupPath`): list of paths in the backup
        package (:obj:`str`): package which created this backup
        package_version (:obj:`str`): version of the package which created this backup
        username (:obj:`str`): name of the user who created this backup
        ip (:obj:`str`): IP address of the computer which created this backup
        date (:obj:`str`): date when this backup was created
    """

    def __init__(self, local_filename='', remote_filename='', paths=None,
                 package=None, package_version=None, username=None, date=None, ip=None):
        """
        Args:
            local_filename (:obj:`str`, optional): path to store the backup
            remote_filename (:obj:`str`, optional): remote name of backup
            paths (obj:`list` of :obj:`BackupPath`, optional): list of paths in the backup
            package (:obj:`str`, optional): package which created this backup
            package_version (:obj:`str`, optional): version of the package which created this backup
            username (:obj:`str`, optional): name of the user who created this backup
            ip (:obj:`str`, optional): IP address of the computer which created this backup
            date (:obj:`str`, optional): date when this backup was created
        """
        self.local_filename = local_filename
        self.remote_filename = remote_filename
        self.paths = paths or []
        self.package = package
        self.package_version = package_version
        self.username = username
        self.ip = ip
        self.date = date

    def set_package(self, repo_path='.'):
        """ Set the package and version from a Git repository

        Args:
            repo_path (:obj:`path`): path to repository
        """
        md = wc_utils.util.git.get_repo_metadata(repo_path)
        self.package = md.url
        self.package_version = str(md.branch) + ':' + str(md.revision)

    def set_username_ip_date(self):
        """ Se the username, IP, and date from the current username, IP, and date """

        # username
        self.username = getpass.getuser()

        # IP address
        sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sckt.connect(("8.8.8.8", 80))
        self.ip = sckt.getsockname()[0]
        sckt.close()

        # date
        self.date = datetime.datetime.utcnow()


class BackupPath(object):
    """ A path in a backup

    Attributes:
        path (:obj:`str`): local path
        arc_path (:obj:`str`): path within the archive
    """

    def __init__(self, path, arc_path):
        """
        Args:
            path (:obj:`str`): local path
            arc_path (:obj:`str`): path within the archive
        """
        self.path = path
        self.arc_path = arc_path
