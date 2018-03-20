""" Git utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

import importlib
git = importlib.import_module('git', package='gitpython')


def get_repo_metadata(dirname='.'):
    """ Get meta data about a repository

    Args:
        dirname (:obj:`str`): path to Git repository

    Returns:
        :obj:`RepositoryMetadata`: repository meta data
    """
    repo = git.Repo(dirname)
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
