""" Git utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017, Karr Lab
:License: MIT
"""

import pygit2


def get_repo_metadata(dirname='.'):
    """ Get meta data about a repository

    Args:
        dirname (:obj:`str`): path to Git repository

    Returns:
        :obj:`RepositoryMetadata`: repository meta data
    """
    repo = pygit2.Repository(dirname)
    origin = next(remote for remote in repo.remotes if remote.name == 'origin')
    url = origin.url
    branch = repo.head.shorthand
    revision = repo.head.target

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
