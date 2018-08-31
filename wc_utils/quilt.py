"""
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-08-03
:Copyright: 2018, Karr Lab
:License: MIT
"""

try:
    import capturer
except ModuleNotFoundError:  # pragma: no cover
    capturer = None  # pragma: no cover
import importlib
import os
try:
    import quilt
except ModuleNotFoundError:  # pragma: no cover
    quilt = None  # pragma: no cover
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
        # check that Quilt is installed
        if not quilt:
            raise ModuleNotFoundError('Quilt must be installed. Run `pip install quilt`')  # pragma: no cover

        # initialize manager
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
        if capturer and not self.verbose:
            capture_output = capturer.CaptureOutput(relay=False)
            capture_output.start_capture()

        quilt.build(self.get_owner_package(), config_filename)
        quilt.login_with_token(self.token)
        quilt.push(self.get_owner_package(), is_public=True, is_team=False)

        if capturer and not self.verbose:
            capture_output.finish_capture()

    def download(self, file_path=None):
        """ Download Quilt package or, optionally, a single path within the package

        Args:
            file_path (:obj:`str`, optional): if provided, download a specific path
                within the package (e.g. `subdir/subsubdir/filename.ext`) rather
                than downloading the entire package

        Raises:
            :obj:`ValueError`: if a specific file is requested, but there is no
                file with the same path within the package
        """
        pkg_name = self.get_owner_package()
        if file_path:
            pkg_path = self.get_package_path(file_path)
            if pkg_path is None:
                raise ValueError('{} does not contain a file with the path `{}`'.format(
                    pkg_name, file_path))
            pkg_name_path = pkg_name + '/' + pkg_path
        else:
            pkg_name_path = pkg_name

        if capturer and not self.verbose:
            capture_output = capturer.CaptureOutput(relay=False)
            capture_output.start_capture()

        quilt.login_with_token(self.token)
        quilt.install(pkg_name_path, force=True, meta_only=False)
        quilt.export(pkg_name_path, output_path=self.path,
                     force=True)

        if capturer and not self.verbose:
            capture_output.finish_capture()

    def get_package_path(self, file_path):
        """ Get the path for a file within the Quilt package

        Args:
            file_path (:obj:`str`): path to file

        Returns:
            :obj:`str`: path within Quilt package
        """
        pkg_name = self.get_owner_package()

        if capturer and not self.verbose:
            capture_output = capturer.CaptureOutput(relay=False)
            capture_output.start_capture()
        quilt.install(pkg_name, force=True, meta_only=True)
        if capturer and not self.verbose:
            capture_output.finish_capture()

        pkg = importlib.import_module('quilt.data.' + pkg_name.replace('/', '.'))

        nodes_to_visit = [((), pkg)]
        while nodes_to_visit:
            parent_pkg_path, parent = nodes_to_visit.pop()
            for child_name, child in parent._items():
                if isinstance(child, quilt.nodes.DataNode):
                    if child._meta['_system']['filepath'] == file_path:
                        return '/'.join(list(parent_pkg_path) + [child_name])
                elif isinstance(child, quilt.nodes.GroupNode):
                    nodes_to_visit.append((
                        tuple(list(parent_pkg_path) + [child_name]),
                        child))

        return None

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
                    node_name = sub_dirname.replace('.', '__DOT__')

                    if node_name in dir_contents:
                        dir_contents = dir_contents[node_name]
                    else:
                        dir_contents[node_name] = {}
                        dir_contents = dir_contents[node_name]

            for filename in filenames:
                if rel_dirname == '.':
                    full_filename = filename
                else:
                    full_filename = os.path.join(rel_dirname, filename)
                basename, ext = os.path.splitext(filename)
                node_name = basename.replace('.', '__DOT__')

                dir_contents[node_name] = {
                    'file': full_filename,
                }

                if ext in ['.csv', '.ssv', '.tsv']:
                    dir_contents[node_name]['transform'] = ext[1:]
                elif ext != '.md':
                    dir_contents[node_name]['transform'] = 'id'

        return config

    def get_owner_package(self):
        """ Get the full identifier (owner/package) of the Quilt package

        Returns:
            :obj:`str`: full identifier of the Quilt package
        """
        return '{}/{}'.format(self.owner, self.package)

    def get_token(self):
        """ Get token

        Returns
            :obj:`str`: authentication token for Quilt user
        """
        config = wc_utils.config.get_config()['wc_utils']['quilt']

        endpoint = 'https://pkg.quiltdata.com/api'
        result = requests.post(endpoint + '/login', json={
            'username': config['username'],
            'password': config['password'],
        })
        result.raise_for_status()
        self.token = result.json()['token']
        return self.token
