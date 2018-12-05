"""
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-08-03
:Copyright: 2018, Karr Lab
:License: MIT
"""

import abduct
import importlib
import os
try:
    import quilt
    quilt._DEV_MODE = True
except ModuleNotFoundError:  # pragma: no cover
    quilt = None  # pragma: no cover
import re
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

        Raises:
            :obj:`ModuleNotFoundError`: if Quilt is not installed
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
        with abduct.captured(abduct.out(tee=self.verbose)):
            quilt.build(self.get_owner_package(), config_filename)
            quilt.login_with_token(self.token)
            quilt.push(self.get_owner_package(), is_public=True, is_team=False)

        # correct file permissions of Quilt package
        quilt_cache = os.path.expanduser(os.path.join('~', '.local', 'share', 'QuiltCli', 'quilt_packages', 'objs'))
        for filename in os.listdir(quilt_cache):
            os.chmod(os.path.join(quilt_cache, filename), 0o664)

    def download(self, system_path=None, sym_links=False):
        """ Download Quilt package or, optionally, a single path within the package

        Args:
            system_path (:obj:`str`, optional): if provided, download a specific path
                within the package (e.g. `subdir/subsubdir/filename.ext`) rather
                than downloading the entire package
            sym_links (:obj:`bool`, optional): if :obj:`True`, export files as symbolic links

        Raises:
            :obj:`ValueError`: if a specific file is requested, but there is no
                file with the same path within the package
        """
        pkg_name = self.get_owner_package()
        if system_path:
            pkg_path = self.get_package_path(system_path)
            if pkg_path is None:
                raise ValueError('{} does not contain a file with the path `{}`'.format(
                    pkg_name, system_path))
            pkg_name_path = pkg_name + '/' + pkg_path
        else:
            pkg_name_path = pkg_name

        with abduct.captured(abduct.out(tee=self.verbose)):
            quilt.login_with_token(self.token)
            quilt.install(pkg_name_path, force=True, meta_only=False)
            quilt.export(pkg_name_path, output_path=self.path,
                         force=True, symlinks=sym_links)

    def get_package_path(self, system_path):
        """ Get the path for a file or directory within the Quilt package

        Args:
            system_path (:obj:`str`): path to file or directory

        Returns:
            :obj:`str`: corresponding path within Quilt package to file or directory
        """
        system_path = re.sub('/+$', '', system_path)
        pkg_name = self.get_owner_package()

        with abduct.captured(abduct.out(tee=self.verbose)):
            quilt.install(pkg_name, force=True, meta_only=True)

        pkg = importlib.import_module('quilt.data.' + pkg_name.replace('/', '.'))

        nodes_to_visit = [((), pkg)]
        while nodes_to_visit:
            parent_pkg_path, parent = nodes_to_visit.pop()
            for child_name, child in parent._items():
                if isinstance(child, quilt.nodes.DataNode):
                    if child._meta['_system']['filepath'].startswith(system_path + '/'):
                        n_parts = system_path.count('/') + 1
                        pkg_path = list(parent_pkg_path) + [child_name]
                        return '/'.join(pkg_path[0:n_parts])
                    elif child._meta['_system']['filepath'] == system_path:
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

        Raises:
            :obj:`ValueError`: if Quilt node names will not be unique or there a directory is empty
        """
        config = {}
        contents = config['contents'] = {}

        dir_node_names = {}

        for abs_dirname, subdirnames, filenames in os.walk(self.path):
            rel_dirname = os.path.relpath(abs_dirname, self.path)

            dir_contents = contents
            if rel_dirname != '.':
                for sub_dirname in rel_dirname.split(os.sep):
                    node_name = re.sub('[^a-z0-9_]', self._unique_node_name_replace_func, sub_dirname, flags=re.IGNORECASE)

                    if node_name not in dir_contents:
                        dir_contents[node_name] = {}
                    dir_contents = dir_contents[node_name]

                    if node_name in dir_node_names and dir_node_names[node_name] != sub_dirname:
                        raise ValueError('Directory node name "{}" is not unique'.format(sub_dirname))
                    dir_node_names[node_name] = sub_dirname

            if not subdirnames and not filenames:
                raise ValueError('Quilt does not support empty directories: {}'.format(rel_dirname))

            for filename in filenames:
                if rel_dirname == '.':
                    full_filename = filename
                else:
                    full_filename = os.path.join(rel_dirname, filename)

                node_name = re.sub('[^a-z0-9_]', self._unique_node_name_replace_func, filename, flags=re.IGNORECASE)

                if node_name in dir_contents:
                    raise ValueError('File node name "{}" is not unique'.format(node_name))

                dir_contents[node_name] = {
                    'file': full_filename,
                }

                basename, ext = os.path.splitext(filename)
                if ext in ['.csv', '.ssv', '.tsv']:
                    dir_contents[node_name]['transform'] = ext[1:]
                elif ext != '.md':
                    dir_contents[node_name]['transform'] = 'id'

        return config

    @staticmethod
    def _unique_node_name_replace_func(match):
        """
        Args:
            match (:obj:`re.MatchObject`): regular expression match to a non-alphanumeric character
                that can't be contained in the name of a Quilt node

        Returns:
            :obj:`str`: encoded character for substitution into the name of the Quilt node
        """
        return '__' + str(ord(match.group(0))) + '__'

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
