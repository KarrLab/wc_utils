""" Git utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

import importlib
git = importlib.import_module('git', package='gitpython')
import itertools
import os
import pathlib


def get_repo_metadata(dirname='.', search_parent_directories=True):
    """ Get meta data about a repository

    Args:
        dirname (:obj:`str`): path to Git repository
        search_parent_directories (:obj:`bool`, optional): if :obj:`True`, search for the root 
            of the repository among the parent directories of :obj:`dirname`

    Returns:
        :obj:`RepositoryMetadata`: repository meta data

    Raises:
        :obj:`ValueError`: if obj:`dirname` is not a path to a Git repository
    """
    repo = None
    pure_path = pathlib.PurePath(os.path.abspath(dirname))
    parent_dirnames = itertools.chain([os.path.abspath(dirname)], pure_path.parents)
    for parent_dirname in parent_dirnames:
        try:
            repo = git.Repo(str(parent_dirname), search_parent_directories=search_parent_directories)
            break
        except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
            pass

    if not repo:
        raise ValueError('"{}" is not a Git repository'.format(dirname))
    url = str(repo.remote('origin').url)
    branch = str(repo.active_branch.name)
    revision = str(repo.head.commit.hexsha)
    return RepositoryMetadata(url, branch, revision)


class RepositoryMetadata(object):
    """ Represents meta data about a Git repository

    Attributes:
        url (:obj:`str`): URL
        branch (:obj:`str`): branch
        revision (:obj:`str`): revision
    """

    def __init__(self, url, branch, revision):
        """
        Args:
            url (:obj:`str`): URL
            branch (:obj:`str`): branch
            revision (:obj:`str`): revision
        """
        self.url = url
        self.branch = branch
        self.revision = revision
