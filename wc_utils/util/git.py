""" Git utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2018, Karr Lab
:License: MIT
"""

import dulwich.repo
import six


def get_repo_metadata(dirname='.'):
    """ Get meta data about a repository

    Args:
        dirname (:obj:`str`): path to Git repository

    Returns:
        :obj:`RepositoryMetadata`: repository meta data
    """
    repo = dulwich.repo.Repo(dirname)
    if six.PY2:
        url = repo.get_config()[('remote', 'origin')]['url']
        branch = repo.refs.follow('HEAD')[0][1].rpartition('refs/heads/')[2]
        revision = repo.head()
    else:
        url = repo.get_config()[(b'remote', b'origin')][b'url'].decode()
        branch = repo.refs.follow(b'HEAD')[0][1].rpartition(b'refs/heads/')[2].decode()
        revision = repo.head().decode()
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
