""" Git utilities for obtaining repo metadata

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2019, Karr Lab
:License: MIT
"""

from enum import Enum, auto
from github.GithubException import UnknownObjectException
from pathlib import Path
from wc_utils.config import core
from wc_utils.util.misc import obj_to_str
import git
import github
import itertools
import os


def get_repo(path='.', search_parent_directories=True):
    """ Get a Git repository

    Args:
        path (:obj:`str`): path to file or directory in a Git repository; if `path` doesn't exist
            or is a file then its directory is used
        search_parent_directories (:obj:`bool`, optional): if :obj:`True` have :obj:`git.Repo` search
            for the root of the repository among the parent directories of :obj:`path`; otherwise,
            this method iterates over the parent directories itself

    Returns:
        :obj:`git.Repo`: a `GitPython` repository

    Raises:
        :obj:`ValueError`: if obj:`path` is not a path to a Git repository
    """
    repo = None
    resolved_path = Path(path).expanduser().resolve()
    if not resolved_path.exists() or resolved_path.is_file():
        resolved_path = resolved_path.parent
    dirnames = itertools.chain([str(resolved_path)], resolved_path.parents)
    if search_parent_directories:
        dirnames = [str(resolved_path)]
    for parent_dirname in dirnames:
        try:
            repo = git.Repo(str(parent_dirname), search_parent_directories=search_parent_directories)
            break
        except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError) as e:
            pass

    if not repo:
        raise ValueError('"{}" is not in a Git repository'.format(path))
    return repo


class RepoMetadataCollectionType(Enum):
    """ Type of Git repo being queried for metadata that's stored in a data file """
    DATA_REPO = auto()
    SCHEMA_REPO = auto()


# todo: automatically determine branch of repo & use it instead of 'master'
def repo_suitability(repo, repo_type, data_file=None):
    """ Evaluate whether a repo is a suitable source for git metadata

    Determine whether `repo` is in a state that's suitable for collecting metadata for
    a data file. It cannot be ahead of the remote, because commits must have been pushed to
    the server so they can be later retrieved.
    If the `repo_type` is `RepoMetadataCollectionType.SCHEMA_REPO`, then there cannot be any differences
    between the index and the working tree because the schema should be synched with the origin.
    If the`repo_type` is `RepoMetadataCollectionType.DATA_REPO` then the repo can contain changes,
    but the data file should not depend on them. The caller is responsible for determining this.

    Args:
        repo (:obj:`git.Repo`): a `GitPython` repository
        repo_type (:obj:`RepoMetadataCollectionType`): repo type having status determined
        data_file (:obj:`str`, optional): pathname of a data file in the repo; must be provided if
            `repo_type` is `RepoMetadataCollectionType.DATA_REPO`

    Returns:
        :obj:`list` of :obj:`str`: list of reasons, if any, that the repo is in a state that's not
            suitable for collecting metadata; an empty list indicates that the repo can be used to
            collect metadata
    """
    unsuitable_changes = []
    commits_ahead = list(repo.iter_commits('origin/master..master'))
    if commits_ahead:
        unsuitable_changes.append('commits ahead of origin')

    # diff between the index and the commit tree HEAD points to
    diff_index = repo.index.diff(repo.head.commit)
    if repo_type is RepoMetadataCollectionType.DATA_REPO:

        if not data_file:
            raise ValueError("data_file must be provided if repo_type is "
                "RepoMetadataCollectionType.DATA_REPO")

        # ensure that data_file exists in repo
        resolved_data_file = Path(data_file).expanduser().resolve()
        repo_root = Path(repo.git_dir).parent
        try:
            resolved_data_file.relative_to(str(repo_root))
        except ValueError:
            raise ValueError("data_file '{}' must be in the repo that's in '{}'".format(
                data_file, str(repo_root)))

        # ideally, the git repo storing a data file should only have changes in the data file so that
        # it depends on the prior commits; but this may be difficult to satisfy, so other differences
        # should be reported as a warning
        for change_type in diff_index.change_type:
            for diff in diff_index.iter_change_type(change_type):
                resolved_a_rawpath = repo_root.joinpath(diff.a_rawpath.decode())
                resolved_b_rawpath = repo_root.joinpath(diff.b_rawpath.decode())
                if (resolved_a_rawpath != resolved_data_file or
                    resolved_b_rawpath != resolved_data_file):
                    unsuitable_changes.append('modified path(s) are not data_file path')

        for untracked_file in repo.untracked_files:
            if repo_root.joinpath(untracked_file) != resolved_data_file:
                unsuitable_changes.append("untracked file '{}' is not data file: '{}'".format(
                    repo_root.joinpath(untracked_file), resolved_data_file))

    elif repo_type is RepoMetadataCollectionType.SCHEMA_REPO:

        # a schema repo that has any differences between the index and the working tree
        # isn't suitable for collecting metadata
        for change_type in diff_index.change_type:
            if list(diff_index.iter_change_type(change_type)):
                unsuitable_changes.append('changes present')
        if repo.untracked_files:
            unsuitable_changes.append('untracked files present')

    else:
        raise ValueError("Invalid RepoMetadataCollectionType: '{}'".format(repo_type))

    return unsuitable_changes


def get_repo_metadata(path='.', search_parent_directories=True, repo_type=None, data_file=None):
    """ Get metadata about a Git repository

    Args:
        path (:obj:`str`): path to file or directory in a Git repository
        search_parent_directories (:obj:`bool`, optional): if :obj:`True`, have `GitPython` search for
            the root of the repository among the parent directories of :obj:`path`
        repo_type (:obj:`RepoMetadataCollectionType`, optional): repo type having metadata collected
        data_file (:obj:`str`, optional): pathname of a data file in the repo; must be provided if
            `repo_type` is `RepoMetadataCollectionType.DATA_REPO`

    Returns:
        :obj:`tuple`: of :obj:`RepositoryMetadata`:, :obj:`list` of :obj:`str`: repository metadata,
            and, if `repo_type` is provided, changes in the repository that make it unsuitable

    Raises:
        :obj:`ValueError`: if obj:`path` is not a path in a Git repository,
            or if the repo is not suitable for gathering metadata
    """
    repo = get_repo(path=path, search_parent_directories=search_parent_directories)
    unsuitable_changes = None
    if repo_type:
        unsuitable_changes = repo_suitability(repo, repo_type, data_file=data_file)

    url = str(repo.remote('origin').url)
    branch = str(repo.active_branch.name)
    revision = str(repo.head.commit.hexsha)
    return RepositoryMetadata(url, branch, revision), unsuitable_changes


class RepositoryMetadata(object):
    """ Represents metadata about a Git repository

    Attributes:
        url (:obj:`str`): URL
        branch (:obj:`str`): branch
        revision (:obj:`str`): revision
    """
    ATTRIBUTES = ['url', 'branch', 'revision']

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

    def __eq__(self, other):
        """ Compare two repository metadata objects

        Args:
            other (:obj:`RepositoryMetadata`): other repository metadata objects

        Returns:
            :obj:`bool`: true if repository metadata objects are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        for attr in self.ATTRIBUTES:
            if getattr(other, attr) != getattr(self, attr):
                return False

        return True

    def __ne__(self, other):
        """ Compare two repository metadata objects

        Args:
            other (:obj:`RepositoryMetadata`): other repository metadata objects

        Returns:
            :obj:`bool`: true if repository metadata objects are semantically unequal
        """
        return not self.__eq__(other)

    def __str__(self):
        """ Get string representation of a repository metadata object

        Returns:
            :obj:`str`: string representation of a repository metadata object
        """
        return obj_to_str(self, self.ATTRIBUTES)


class GitHubRepoForTests(object):
    """ Functions for managing test GitHub repos """

    @staticmethod
    def get_github_api_token():
        config = core.get_config()['wc_utils']['github']
        return config['github_api_token']

    def __init__(self, name, organization='KarrLab'):
        """ Manage a test GitHub repository

        Args:
            name (:obj:`str`): name of the repo
            organization (:obj:`str`): GitHub organization home for the repo; default='KarrLab'
        """
        self.api_token = self.get_github_api_token()
        self.name = name
        self.organization = organization

    def make_test_repo(self, dirname=None):
        """ Create a test GitHub repository

        Args:
            dirname (:obj:`str`, optional): a directory name; if present, clone the repo into it

        Returns:
            :obj:`obj`: if `dirname` is provided, a `gitpython` reference to a local clone of the test
                GitHub repository; otherwise, the URL of the test GitHub repository
        """
        # delete test repo in case it wasn't deleted previously
        self.delete_test_repo()
        g = github.Github(self.api_token)
        org = g.get_organization(self.organization)
        org.create_repo(name=self.name, private=False, auto_init=True)
        repo_url = 'https://github.com/{}/{}.git'.format(self.organization, self.name)
        if dirname:
            # clone from GitHub
            self.repo = git.Repo.clone_from(repo_url, dirname)
            return self.repo
        return repo_url

    def delete_test_repo(self):
        g = github.Github(self.api_token)
        try:
            repo = g.get_repo("{}/{}".format(self.organization, self.name))
            repo.delete()
        except UnknownObjectException:
            # ignore exception that occurs when delete does not find the repo
            pass
        except Exception:   # pragma: no cover; cannot deliberately raise an other exception
            # re-raise all other exceptions
            raise
