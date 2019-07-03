""" Test of Git utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2019, Karr Lab
:License: MIT
"""

import git
from wc_utils.util.git import (get_repo, get_repo_metadata, repo_suitability, RepoMetadataCollectionType,
    GitHubRepoForTests)
import shutil
import tempfile
import os
import unittest
from pathlib import Path


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
        self.assertTrue(isinstance(get_repo(path='.'), git.Repo))
        self.assertTrue(isinstance(get_repo(path=os.path.dirname(__file__)), git.Repo))

        repo = get_repo(path=os.path.dirname(__file__), search_parent_directories=False)
        self.assertTrue(isinstance(repo, git.Repo))

        self.assertTrue(isinstance(get_repo(__file__), git.Repo))

        repo = get_repo(path=os.path.join(os.path.dirname(__file__), 'no such file'))
        self.assertTrue(isinstance(repo, git.Repo))

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, 'is not in a Git repository'):
                get_repo(path=temp_dir)

    def test_repo_suitability(self):
        # cache repo type names
        DATA_REPO = RepoMetadataCollectionType.DATA_REPO
        SCHEMA_REPO = RepoMetadataCollectionType.SCHEMA_REPO

        # both data_repo and schema_repo should not return unsuitable_changes on a clean repo
        self.assertFalse(repo_suitability(self.repo, DATA_REPO, data_file=self.test_file))
        self.assertFalse(repo_suitability(self.repo, SCHEMA_REPO))

        # write & add the data file
        with open(self.test_file, 'w') as f:
            f.write('hello world!')
        self.repo.index.add([self.test_file])

        # schema_repo should return unsuitable_changes
        self.assertTrue(repo_suitability(self.repo, SCHEMA_REPO))
        # data_repo with data_file=<test file> should not return unsuitable_changes
        self.assertFalse(repo_suitability(self.repo, DATA_REPO, data_file=self.test_file))
        # data_repo with data_file=<path to other file> should return unsuitable_changes
        other_test_file = str(Path(self.repo.git_dir).parent / 'other_test.txt')
        self.assertTrue(repo_suitability(self.repo, DATA_REPO, data_file=other_test_file))

        # write an untracked file
        with open(other_test_file, 'w') as f:
            f.write('hello world!')
        # data_repo with an untracked file != data_file should return unsuitable_changes
        self.assertTrue(repo_suitability(self.repo, DATA_REPO, data_file=self.test_file))
        # data_repo with an untracked file == data_file should return unsuitable_changes
        self.assertTrue(repo_suitability(self.repo, DATA_REPO, data_file=other_test_file))
        # schema_repo an untracked file should return unsuitable_changes
        self.assertTrue(repo_suitability(self.repo, SCHEMA_REPO))
        os.remove(other_test_file)

        # commit changes
        self.repo.index.commit("commit changes to test_file")

        # schema_repo and data_repo should return unsuitable_changes because commits haven't been pushed
        self.assertTrue(repo_suitability(self.repo, SCHEMA_REPO))
        self.assertTrue(repo_suitability(self.repo, DATA_REPO, data_file=self.test_file))

        # data_repo with file not in repo should raise exception
        with self.assertRaisesRegex(ValueError, r"data_file '.+' must be in the repo that's in '.+'"):
            repo_suitability(self.repo, DATA_REPO, data_file='/tmp/test.xlsx')

        repo = get_repo(path='.')
        with self.assertRaisesRegex(ValueError, "data_file must be provided if repo_type is "
                "RepoMetadataCollectionType.DATA_REPO"):
            repo_suitability(repo, DATA_REPO)

        with self.assertRaisesRegex(ValueError, "Invalid RepoMetadataCollectionType"):
            repo_suitability(repo, 3)

    def test_get_repo_metadata(self):
        md, unsuitable_changes = get_repo_metadata(path='.')
        self.assertIn(md.url, [
            'https://github.com/KarrLab/wc_utils.git',
            'ssh://git@github.com/KarrLab/wc_utils.git',
            'git@github.com:KarrLab/wc_utils.git',
        ])
        self.assertEqual(md.branch, 'master')
        self.assertIn('branch: master', str(md))
        self.assertEqual(unsuitable_changes, None)

        md, unsuitable_changes = get_repo_metadata(path=self.tempdir,
            repo_type=RepoMetadataCollectionType.SCHEMA_REPO)
        self.assertIn('KarrLab/test_wc_utils_git.git', md.url)
        self.assertEqual(md.branch, 'master')


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
