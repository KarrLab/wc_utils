""" Git utilities for obtaining repo metadata

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2019, Karr Lab
:License: MIT
"""

import git
import itertools
import os
from pathlib import Path
from enum import Enum, auto


def get_repo(dirname='.', search_parent_directories=True):
    """ Get a Git repository

    Args:
        dirname (:obj:`str`): path to Git repository
        search_parent_directories (:obj:`bool`, optional): if :obj:`True`, search for the root 
            of the repository among the parent directories of :obj:`dirname`; default=:obj:`True`

    Returns:
        :obj:`git.Repo`: a `GitPython` repository

    Raises:
        :obj:`ValueError`: if obj:`dirname` is not a path to a Git repository
    """
    repo = None
    resolved_path = Path(dirname).expanduser().resolve()
    dirnames = itertools.chain([str(resolved_path)], resolved_path.parents)
    if search_parent_directories:
        dirnames = [str(resolved_path)]
    for parent_dirname in dirnames:
        try:
            repo = git.Repo(str(parent_dirname), search_parent_directories=search_parent_directories)
            break
        except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
            pass

    if not repo:
        raise ValueError('"{}" is not in a Git repository'.format(dirname))
    return repo


class RepoMetadataCollectionType(Enum):
    """ Type of Git repo being queried for metadata that's stored in a data file """
    DATA_REPO = auto()
    SCHEMA_REPO = auto()


def repo_status(repo, repo_type, data_file=None):
    """ Get status of a repo

    Determine whether `repo` is in a state that allows it to be used to collect metadata for
    a data file. It cannot be ahead of the remote, because versions must have been committed to
    the server so they can be later retrieved. And it cannot have local changes, except for
    changes to a data file that we expect will be later committed and pushed.

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
            raise ValueError("data_file '{}' must be in the repo that's in '{}'".format(data_file, str(repo_root)))

        # a data repo that's suitable for collecting metadata may only have differences between the
        # index and the working tree in the data_file
        for change_type in diff_index.change_type:
            for diff in diff_index.iter_change_type(change_type):
                resolved_a_rawpath = repo_root.joinpath(diff.a_rawpath.decode())
                resolved_b_rawpath = repo_root.joinpath(diff.b_rawpath.decode())
                if (resolved_a_rawpath != resolved_data_file or
                    resolved_b_rawpath != resolved_data_file):
                    unsuitable_changes.append('modified path(s) are not data_file path')

        for untracked_file in repo.untracked_files:
            if repo_root.joinpath(untracked_file) != resolved_data_file:
                unsuitable_changes.append('untracked file is not data_file path')

    elif repo_type is RepoMetadataCollectionType.SCHEMA_REPO:

        # a schema repo that has any differences between the index and the working tree
        # isn't suitable for collecting metadata
        for change_type in diff_index.change_type:
            if list(diff_index.iter_change_type(change_type)):
                unsuitable_changes.append('changes present')
        if repo.untracked_files:
            unsuitable_changes.append('untracked files present')

    else:   # pragma: no cover
        raise ValueError("Invalid RepoMetadataCollectionType: '{}'".format(repo_type.name))

    return unsuitable_changes


def get_repo_metadata(dirname='.', search_parent_directories=True, repo_type=None, data_file=None):
    """ Get metadata about a Git repository

    Args:
        dirname (:obj:`str`): path to Git repository
        search_parent_directories (:obj:`bool`, optional): if :obj:`True`, have `GitPython` search for
            the root of the repository among the parent directories of :obj:`dirname`
        repo_type (:obj:`RepoMetadataCollectionType`, optional): repo type having status determined
        data_file (:obj:`str`, optional): pathname of a data file in the repo; must be provided if
            `repo_type` is `RepoMetadataCollectionType.DATA_REPO`

    Returns:
        :obj:`RepositoryMetadata`: repository metadata

    Raises:
        :obj:`ValueError`: if obj:`dirname` is not a path to a Git repository,
            or if the repo is not suitable for gathering metadata
    """
    repo = get_repo(dirname=dirname, search_parent_directories=search_parent_directories)
    if repo_type:
        unsuitable_changes = repo_status(repo, repo_type, data_file=data_file)
        if unsuitable_changes:
            raise ValueError("Cannot gather metadata from Git repo in '{}'".format(dirname))

    url = str(repo.remote('origin').url)
    branch = str(repo.active_branch.name)
    revision = str(repo.head.commit.hexsha)
    return RepositoryMetadata(url, branch, revision)


class RepositoryMetadata(object):
    """ Represents metadata about a Git repository

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

    def __str__(self):
        """ Get string representation of metadata

        Returns:
            :obj:`str`: string representation of metadata
        """
        lines = []
        for attr in ['url', 'branch', 'revision']:
            lines.append("{}: {}".format(attr, getattr(self, attr)))
        return '\n'.join(lines)
