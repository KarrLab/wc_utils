"""
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-03
:Copyright: 2017, Karr Lab
:License: MIT
"""

import datetime
import getpass
import io
import json
import os
import pygit2
import requests
import shutil
import six
import socket
import tarfile
import tempfile
import wc_utils.util.git


class BackupManager(object):
    """ Manages backups of files to the Karr Lab code server

    Attributes:
        archive_filename (:obj:`str`): path to store the backup
        archive_remote_filename (:obj:`str`): remote name of backup
        endpoint (:obj:`str`): URL to upload/download backups
        token (:obj:`str`): server login token
    """

    DEFAULT_ENDPOINT = 'http://code.karrlab.org/data'
    # :obj:`str`: default URL to upload/download backups

    def __init__(self, archive_filename, archive_remote_filename,
                 endpoint=DEFAULT_ENDPOINT, token=''):
        """
        Args:
            archive_filename (:obj:`str`): path to store the backup
            archive_remote_filename (:obj:`str`): remote name of backup            
            endpoint (:obj:`str`, optional): URL to upload/download backups
            token (:obj:`str`, optional): server login token
        """
        if not token:
            token = os.getenv('CODE_SERVER_TOKEN')

        self.archive_filename = archive_filename
        self.archive_remote_filename = archive_remote_filename
        self.endpoint = endpoint
        self.token = token

    def create(self, files):
        """ Create gzipped backup of the file

        Args:
            files (:obj:`list` of :obj:`BackupFile`): list of files to backup and their metadata

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        with tarfile.open(self.archive_filename, "w:gz") as tar:
            for file in files:
                tar.add(file.filename, arcname=file.arcname)

                _, temp_filename = tempfile.mkstemp()
                with open(temp_filename, 'w') as temp_file:
                    json.dump({
                        'filename': file.filename,
                        'arcname': file.arcname,
                        'created': file.created,
                        'modified': file.modified,
                        'username': file.username,
                        'ip': file.ip,
                        'program': file.program,
                        'version': file.version,
                    }, temp_file)
                tar.add(temp_filename, arcname=file.arcname + '.json')
                os.remove(temp_filename)

        return self

    def extract(self, files):
        """ Extract the files from the backup and update the metadata of :obj:`files`.

        Args:
            files (:obj:`list` of :obj:`BackupFile`): list of files to backup and their metadata

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        with tarfile.open(self.archive_filename, "r:gz") as tar:
            tempdir = tempfile.mkdtemp()
            tar.extractall(tempdir)
            for file in files:
                os.rename(os.path.join(tempdir, file.arcname), file.filename)

                with open(os.path.join(tempdir, file.arcname + '.json'), 'r') as json_file:
                    md = json.load(json_file)
                file.created = md['created']
                file.modified = md[u'modified']
                file.username = md['username']
                file.ip = md['ip']
                file.program = md['program']
                file.version = md['version']
            shutil.rmtree(tempdir)

        return self

    def upload(self):
        """ Upload a backup to a server 

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        response = requests.post(self.endpoint + '/upload.php',
                                 data={
                                     'token': self.token,
                                     'filename': self.archive_remote_filename
                                 },
                                 files=[
                                     ('file', (self.archive_remote_filename, open(self.archive_filename, 'rb'), 'application/x-gzip')),
                                 ])
        response.raise_for_status()

        return self

    def download(self):
        """ Download a backup from the server

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        response = requests.get(self.endpoint + '/download.php', params={'token': self.token, 'filename': self.archive_remote_filename})
        response.raise_for_status()
        with open(self.archive_filename, 'wb') as file:
            file.write(response.content)

        return self

    def cleanup(self):
        """ Remove the archive """
        if os.path.isfile(self.archive_filename):
            os.remove(self.archive_filename)


class BackupFile(object):
    """ Represents the meta data about a backup 

    Attributes:
        filename (:obj:`str`): local path to the file
        arcname (:obj:`str`): name the file within the archive
        program (:obj:`str`): program which created the file
        version (:obj:`str`): program version which created the file
        username (:obj:`str`): name of the user who generated the file
        ip (:obj:`str`): ip address where the file was generated
        created (:obj:`float`): date the file was created
        modified (:obj:`float`): date the file was modified 
    """

    def __init__(self, filename, arcname, program=None, version=None, username=None, ip=None, created=None, modified=None):
        """
        Args:
            filename (:obj:`str`): local path to the file
            arcname (:obj:`str`): name the file within the archive
            program (:obj:`str`, optional): program which created the file
            version (:obj:`str`, optional): program version which created the file
            username (:obj:`str`, optional): name of the user who generated the file
            ip (:obj:`str`, optional): ip address where the file was generated
            created (:obj:`float`, optional): date the file was created
            modified (:obj:`float`, optional): date the file was modified
        """
        self.filename = filename
        self.arcname = arcname
        self.program = program
        self.version = version
        self.username = username
        self.ip = ip
        self.created = created
        self.modified = modified

    def set_created_modified_time(self):
        """ Get the created and modified time """
        self.created = os.path.getctime(self.filename)
        self.modified = os.path.getmtime(self.filename)

    def set_username_ip(self):
        """ The current username and IP """
        self.username = getpass.getuser()
        sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sckt.connect(("8.8.8.8", 80))
        self.ip = sckt.getsockname()[0]
        sckt.close()

    def set_program_version_from_repo(self, repo_path='.'):
        """ Get the program and version from a Git repository

        Args:
            repo_path (:obj:`path`): path to repository
        """
        try:
            md = wc_utils.util.git.get_repo_metadata(repo_path)
            self.program = md.url
            self.version = str(md.branch) + ':' + str(md.revision)
        except KeyError:
            self.program = None
            self.version = None
