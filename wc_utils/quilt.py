"""
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-08-03
:Copyright: 2018, Karr Lab
:License: MIT
"""

import capturer
import os
import quilt
import requests
import wc_utils.config
import yaml


class QuiltManager(object):
    """ Manages uploading and downloading of a Quilt package

    Attributes:
        path (:obj:`str`): local path to save package or buit package from
        package (:obj:`str`): identifier of the Quilt package
        owner (:obj:`str`): identifier of the owner of the Quilt package
        token (:obj:`str`): authentication token for Quilt
        verbose (:obj:`bool`): if :obj:`True`, display Quilt status
    """

    # TODO: support Quilt teams

    def __init__(self, path, package, owner=None, token=None, verbose=None):
        """
        Args:
            path (:obj:`str`): local path to export package or buit package from
            package (:obj:`str`): identifier of the Quilt package
            owner (:obj:`str`, optional): identifier of the owner of the Quilt package
            token (:obj:`str`, optional): authentication token for Quilt
            verbose (:obj:`bool`, optional): if :obj:`True`, display Quilt status
        """
        config = wc_utils.config.get_config()['wc_utils']['quilt']
        self.path = path
        self.package = package
        self.owner = owner or config['owner']
        self.token = token or config['token']
        self.verbose = verbose or config['verbose']

    def upload(self):
        """ Build and upload Quilt package """
        # generate config
        config = self.gen_package_build_config()

        # save config file
        config_filename = os.path.join(self.path, 'build.yml')
        with open(config_filename, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

        # build and push package
        with capturer.CaptureOutput(relay=self.verbose):
            quilt.build(self.get_owner_package(), config_filename)
            quilt.login_with_token(self.token)
            quilt.push(self.get_owner_package(), is_public=True, is_team=False)

    def download(self):
        """ Download Quilt package """
        with capturer.CaptureOutput(relay=self.verbose):
            quilt.login_with_token(self.token)
            quilt.install(self.get_owner_package(), force=True, meta_only=False)
            quilt.export(self.get_owner_package(), output_path=self.path, force=True)

    def gen_package_build_config(self):
        """ Generate the build configuration for a package

        * Force Quilt to retain Excel formatting by setting the transform of all `.xls` and `.xlsx` files to `id`

        Returns:
            :obj:`dict`: package build configuration
        """
        config = {}
        contents = config['contents'] = {}

        for abs_dirname, _, filenames in os.walk(self.path):
            rel_dirname = os.path.relpath(abs_dirname, self.path)

            dir_contents = contents
            if rel_dirname != '.':
                for sub_dirname in rel_dirname.split(os.sep):
                    if sub_dirname in dir_contents:
                        dir_contents = dir_contents[sub_dirname]
                    else:
                        dir_contents[sub_dirname] = {}
                        dir_contents = dir_contents[sub_dirname]

            for filename in filenames:
                if rel_dirname == '.':
                    full_filename = filename
                else:
                    full_filename = os.path.join(rel_dirname, filename)
                basename, ext = os.path.splitext(filename)

                dir_contents[basename] = {
                    'file': full_filename,
                }

                if ext in ['.csv', '.ssv', '.tsv']:
                    dir_contents[basename]['transform'] = ext[1:]
                elif ext != '.md':
                    dir_contents[basename]['transform'] = 'id'

        return config

    def get_owner_package(self):
        """ Get the full identifier (owner/package) of the Quilt package

        Returns:
            :obj:`str`: full identifier of the Quilt package
        """
        return '{}/{}'.format(self.owner, self.package)

    def get_token(self, username, password):
        """ Get token

        Args:
            username (:obj:`str`): Quilt user name
            password (:obj:`str`): Quilt password

        Returns
            :obj:`str`: authentication token for Quilt user
        """
        endpoint = 'https://pkg.quiltdata.com/api'
        result = requests.post(endpoint + '/login', json={
            'username': username,
            'password': password,
        })
        result.raise_for_status()
        self.token = result.json()['token']
        return self.token
