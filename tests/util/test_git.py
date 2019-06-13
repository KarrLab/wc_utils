""" Test of Git utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2019, Karr Lab
:License: MIT
"""

import git
from wc_utils.util.git import get_repo, get_repo_metadata, repo_status, RepoMetadataCollectionType
import shutil
import tempfile
import os
import unittest
from pathlib import Path
import github
from github.GithubException import UnknownObjectException
# from .config import core

# todo: put API token in config file
# todo: get push working on CircleCI
RUNNING_ON_CIRCLE = True


# functions for managing test repos
def get_github_api_token():
    '''
    config = core.get_config()['wc_utils']
    return config['github_api_token']
    '''
    return '3-2-3-d-0-9-d-3-0-6-7-3-6-d-a-d-b-4-3-8-f-3-5-6-8-2-e-1-1-5-2-b-7-b-2-e-9-b-5-6'.replace('-', '' )


def make_test_repo(name):
    # create a test GitHub repository in KarrLab
    # return its URL
    g = github.Github(get_github_api_token())
    org = g.get_organization('KarrLab')
    org.create_repo(name=name, private=False, auto_init=True)
    return 'https://github.com/KarrLab/{}.git'.format(name)


def delete_test_repo(name, organization='KarrLab'):
    g = github.Github(get_github_api_token())
    try:
        repo = g.get_repo("{}/{}".format(organization, name))
        repo.delete()
    except UnknownObjectException:
        # ignore exception that occurs when delete does not find the repo
        pass
    except Exception:   # pragma: no cover; cannot deliberately raise an other exception
        # re-raise all other exceptions
        raise


class TestGit(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        # create test repo on GitHub
        self.test_repo_name = 'test_wc_utils_git'
        # delete test repo in case it wasn't deleted previously
        delete_test_repo(self.test_repo_name)
        repo_url = make_test_repo(self.test_repo_name)
        # clone from url
        self.repo = git.Repo.clone_from(repo_url, self.tempdir)

        # create test file path
        Path(self.tempdir).joinpath('test_dir').mkdir()
        self.test_file = str(Path(self.tempdir) / 'test_dir' / 'test.txt')

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        # delete repo from GitHub
        delete_test_repo(self.test_repo_name)

    def test_get_repo(self):
        repo = get_repo(dirname='.')
        self.assertTrue(isinstance(repo, git.Repo))
        repo = get_repo(dirname=os.path.dirname(__file__), search_parent_directories=False)
        self.assertTrue(isinstance(repo, git.Repo))
        repo = get_repo(dirname=os.path.dirname(__file__), search_parent_directories=True)
        self.assertTrue(isinstance(repo, git.Repo))

        tempdir = tempfile.mkdtemp()
        with self.assertRaisesRegex(ValueError, 'is not in a Git repository'):
            get_repo(dirname=tempdir)
        shutil.rmtree(tempdir)

    def test_repo_status(self):
        # both data_repo and schema_repo should return True on a clean repo
        self.assertFalse(repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=self.test_file))
        self.assertFalse(repo_status(self.repo, RepoMetadataCollectionType.SCHEMA_REPO))

        # write & add test file
        with open(self.test_file, 'w') as f:
            f.write('hello world!')
        self.repo.index.add([self.test_file])

        # schema_repo should return False
        self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.SCHEMA_REPO))
        # data_repo with data_file=<test file> should return True
        self.assertFalse(repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=self.test_file))
        # data_repo with data_file=<path to other file> should return False
        other_test_file = str(Path(self.repo.git_dir).parent / 'other_test.txt')
        self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=other_test_file))

        # commit changes
        self.repo.index.add([self.test_file])
        self.repo.index.commit("commit changes to test_file")

        # schema_repo and data_repo should return False because commits haven't been pushed
        self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.SCHEMA_REPO))
        # data_repo with data_file=<test file> should return False
        self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=self.test_file))

        if not RUNNING_ON_CIRCLE:

            # push changes
            origin = self.repo.remotes.origin
            rv = origin.push()

            # create an untracked file
            untracked_file = Path(self.tempdir) / 'test_dir' / 'untracked_file.txt'
            untracked_filename = str(untracked_file)
            open(untracked_filename, 'wb').close()
            # schema_repo should return False
            self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.SCHEMA_REPO))
            # data_repo with data_file=untracked_filename should return True
            self.assertFalse(repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO,
                data_file=untracked_filename))
            # data_repo with data_file=other_test_file should return False
            self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO,
                data_file=other_test_file))
            # delete untracked_file
            untracked_file.unlink()

        # data_repo with file not in repo should raise exception
        with self.assertRaisesRegex(ValueError, r"data_file '.+' must be in the repo that's in '.+'"):
            repo_status(self.repo, RepoMetadataCollectionType.DATA_REPO, data_file='/tmp/test.xlsx')

        repo = get_repo(dirname='.')
        with self.assertRaisesRegex(ValueError, "data_file must be provided if repo_type is "
                "RepoMetadataCollectionType.DATA_REPO"):
            repo_status(repo, RepoMetadataCollectionType.DATA_REPO)

    def test_get_repo_metadata(self):
        md = get_repo_metadata(dirname='.')
        self.assertIn(md.url, [
            'https://github.com/KarrLab/wc_utils.git',
            'ssh://git@github.com/KarrLab/wc_utils.git',
            'git@github.com:KarrLab/wc_utils.git',
        ])
        self.assertEqual(md.branch, 'correct_git_versions')
        self.assertIn('branch: correct_git_versions', str(md))

        md = get_repo_metadata(dirname=self.tempdir, repo_type=RepoMetadataCollectionType.SCHEMA_REPO)
        self.assertIn('KarrLab/test_wc_utils_git.git', md.url)
        self.assertEqual(md.branch, 'master')

        # write & add test file
        with open(self.test_file, 'w') as f:
            f.write('hello world!')

        self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.SCHEMA_REPO))
        with self.assertRaisesRegex(ValueError, "Cannot gather metadata from Git repo"):
            get_repo_metadata(dirname=self.tempdir, repo_type=RepoMetadataCollectionType.SCHEMA_REPO)
