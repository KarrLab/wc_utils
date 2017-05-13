"""
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-03
:Copyright: 2017, Karr Lab
:License: MIT
"""

import os
import requests
import shutil
import tarfile
import tempfile


class BackupManager(object):
    """ Manages backups of files to the Karr Lab code server

    Attributes:
        filename (:obj:`str`): path to backup
        arcname (:obj:`str`): name of the file within the backup
        archive_filename (:obj:`str`): path to store the backup
        archive_remote_filename (:obj:`str`): remote name of backup
        upload_endpoint (:obj:`str`): default URL to upload backups
        download_endpoint (:obj:`str`): default URL to download backups
        token (:obj:`str`): server login token
    """

    DEFAULT_UPLOAD_ENDPOINT = 'http://code.karrlab.org/data/upload.php'
    # :obj:`str`: default URL to upload backups

    DEFAULT_DOWNLOAD_ENDPOINT = 'http://code.karrlab.org/data/download.php'
    # :obj:`str`: default URL to download backups

    def __init__(self, filename, arcname='', archive_filename='', archive_remote_filename='',
                 upload_endpoint=DEFAULT_UPLOAD_ENDPOINT, download_endpoint=DEFAULT_DOWNLOAD_ENDPOINT,
                 token=''):
        """
        Args:
            filename (:obj:`str`): path to backup
            arcname (:obj:`str`, optional): name of the file within the backup
            archive_filename (:obj:`str`, optional): path to store the backup
            archive_remote_filename (:obj:`str`, optional): remote name of backup            
            upload_endpoint (:obj:`str`, optional): default URL to upload backups
            download_endpoint (:obj:`str`, optional): default URL to download backups
            token (:obj:`str`, optional): server login token
        """
        if not arcname:
            arcname = os.path.basename(filename)

        if not archive_filename:
            archive_filename = filename + '.tar.gz'

        if not archive_remote_filename:
            archive_remote_filename = arcname + '.tar.gz'

        if not token:
            token = os.getenv('CODE_SERVER_TOKEN')

        self.filename = filename
        self.arcname = arcname
        self.archive_filename = archive_filename
        self.archive_remote_filename = archive_remote_filename
        self.upload_endpoint = upload_endpoint
        self.download_endpoint = download_endpoint
        self.token = token

    def create(self):
        """ Create gzipped backup of the file

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        with tarfile.open(self.archive_filename, "w:gz") as tar:
            tar.add(self.filename, arcname=self.arcname)

        return self

    def extract(self):
        """ Extract the file from the backup 

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        with tarfile.open(self.archive_filename, "r:gz") as tar:
            tempdir = tempfile.mkdtemp()
            tar.extractall(tempdir)
            os.rename(os.path.join(tempdir, self.arcname), self.filename)
            shutil.rmtree(tempdir)

        return self

    def upload(self):
        """ Upload a backup to a server 

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        response = requests.post(self.upload_endpoint, data={'token': self.token, 'filename': self.archive_remote_filename}, files=[
            ('file', (self.archive_remote_filename, open(self.archive_filename, 'rb'), 'application/x-gzip')),
        ])
        response.raise_for_status()

        return self

    def download(self):
        """ Download a backup from the server

        Returns:
            :obj:`BackupManager`: the backup manager
        """
        response = requests.get(self.download_endpoint, params={'token': self.token, 'filename': self.archive_remote_filename})
        response.raise_for_status()
        with open(self.archive_filename, 'wb') as file:
            file.write(response.content)

        return self

    def cleanup(self):
        """ Remove the archive """
        if os.path.isfile(self.archive_filename):
            os.remove(self.archive_filename)
