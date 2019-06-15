""" Test of Git utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2019, Karr Lab
:License: MIT
"""

import git
from wc_utils.util.git import (get_repo, get_repo_metadata, repo_status, RepoMetadataCollectionType,
    GitHubRepoForTests)
import shutil
import tempfile
import os
import unittest
from pathlib import Path

# todo: next: get push working on CircleCI
RUNNING_ON_CIRCLE = True


# todo: next: rename wc_utils.util.git: update wc_utils, obj_model, wc_kb, wc_sim, & wc_lang
# todo: next: have obj_model's test_utils, and test_io reuse GitHubRepoForTests

class TestGit(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        # create test repo on GitHub
        self.test_repo_name = 'test_wc_utils_git'
        self.test_git_repos = GitHubRepoForTests(self.test_repo_name)
        self.repo = self.test_git_repos.make_test_repo(self.tempdir)

        # create test file path
        Path(self.tempdir).joinpath('test_dir').mkdir()
        self.test_file = str(Path(self.tempdir) / 'test_dir' / 'test.txt')

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        # delete repo from GitHub
        self.test_git_repos.delete_test_repo()

    def test_get_repo(self):
        repo = get_repo(path='.')
        self.assertTrue(isinstance(repo, git.Repo))
        repo = get_repo(path=os.path.dirname(__file__))
        self.assertTrue(isinstance(repo, git.Repo))
        repo = get_repo(path=os.path.dirname(__file__), search_parent_directories=False)
        self.assertTrue(isinstance(repo, git.Repo))
        repo = get_repo(__file__)
        self.assertTrue(isinstance(repo, git.Repo))
        repo = get_repo(path=os.path.join(os.path.dirname(__file__), 'no such file'))
        self.assertTrue(isinstance(repo, git.Repo))

        tempdir = tempfile.mkdtemp()
        with self.assertRaisesRegex(ValueError, 'is not in a Git repository'):
            get_repo(path=tempdir)
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

        repo = get_repo(path='.')
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
        self.assertEqual(md.branch, 'master')
        self.assertIn('branch: master', str(md))

        md = get_repo_metadata(dirname=self.tempdir, repo_type=RepoMetadataCollectionType.SCHEMA_REPO)
        self.assertIn('KarrLab/test_wc_utils_git.git', md.url)
        self.assertEqual(md.branch, 'master')

        # write & add test file
        with open(self.test_file, 'w') as f:
            f.write('hello world!')

        self.assertTrue(repo_status(self.repo, RepoMetadataCollectionType.SCHEMA_REPO))
        with self.assertRaisesRegex(ValueError, "Cannot gather metadata from Git repo"):
            get_repo_metadata(dirname=self.tempdir, repo_type=RepoMetadataCollectionType.SCHEMA_REPO)


class TestGitHubRepoForTests(unittest.TestCase):

    def test(self):
        self.assertTrue(isinstance(GitHubRepoForTests.get_github_api_token(), str))
        tempdir = tempfile.mkdtemp()
        test_repo_name = 'test_wc_utils_git'
        test_github_repo = GitHubRepoForTests(test_repo_name)
        self.assertTrue(isinstance(test_github_repo, GitHubRepoForTests))
        self.assertEqual(test_github_repo.name, test_repo_name)
        repo_url = test_github_repo.make_test_repo()
        self.assertTrue(repo_url.startswith('https://github.com'))
        repo = test_github_repo.make_test_repo(tempdir)
        self.assertTrue(isinstance(repo, git.Repo))
        test_git_repos_2 = GitHubRepoForTests('no such repo')
        test_git_repos_2.delete_test_repo()
        test_github_repo.delete_test_repo()
        shutil.rmtree(tempdir)
