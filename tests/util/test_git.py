""" Test of Git utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017-2019, Karr Lab
:License: MIT
"""

import importlib
gitpython = importlib.import_module('git', package='gitpython')
from wc_utils.util.git import get_repo, get_repo_metadata, repo_status, RepoMetadataCollectionType
import shutil
import tempfile
import os
import unittest
from pathlib import Path


class TestGit(unittest.TestCase):

    def test_get_repo(self):
        repo = get_repo(dirname='.')
        self.assertTrue(isinstance(repo, gitpython.Repo))
        repo = get_repo(dirname=os.path.dirname(__file__), search_parent_directories=False)
        self.assertTrue(isinstance(repo, gitpython.Repo))
        repo = get_repo(dirname=os.path.dirname(__file__), search_parent_directories=True)
        self.assertTrue(isinstance(repo, gitpython.Repo))

        tempdir = tempfile.mkdtemp()
        with self.assertRaisesRegex(ValueError, 'is not in a Git repository'):
            get_repo(dirname=tempdir)
        shutil.rmtree(tempdir)

    def test_repo_status(self):
        tempdir = tempfile.mkdtemp()
        repo = gitpython.Repo.init(tempdir)
        # create & commit a test file
        Path(tempdir).joinpath('test_dir').mkdir()
        test_file = str(Path(tempdir) / 'test_dir' / 'test.txt')
        open(test_file, 'wb').close()
        repo.index.add([test_file])
        repo.index.commit("commit test_file")

        # both data_repo and schema_repo should return True on a clean repo
        self.assertTrue(repo_status(repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=test_file))
        self.assertTrue(repo_status(repo, RepoMetadataCollectionType.SCHEMA_REPO))

        # modify the file
        with open(test_file, 'a') as f:
            f.write('hello world!')
        # schema_repo should return False
        self.assertFalse(repo_status(repo, RepoMetadataCollectionType.SCHEMA_REPO))
        # data_repo with file as data_file should return True
        self.assertTrue(repo_status(repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=test_file))
        # data_repo with other file as data_file should return False
        other_test_file = str(Path(repo.git_dir).parent / 'other_test.txt')
        self.assertFalse(repo_status(repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=other_test_file))
        # commit changes
        repo.index.add([test_file])
        repo.index.commit("commit changes to test_file")

        # create an untracked file
        untracked_file = str(Path(tempdir) / 'test_dir' / 'untracked_file.txt')
        open(untracked_file, 'wb').close()
        # schema_repo should return False
        self.assertFalse(repo_status(repo, RepoMetadataCollectionType.SCHEMA_REPO))
        # data_repo with data_file=untracked_file should return True
        self.assertTrue(repo_status(repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=untracked_file))
        # data_repo with data_file=other_test_file should return False
        self.assertFalse(repo_status(repo, RepoMetadataCollectionType.DATA_REPO,
            data_file=other_test_file))

        # data_repo with file not in repo should raise exception
        with self.assertRaisesRegex(ValueError, r"data_file '.+' must be in the repo that's in '.+'"):
            repo_status(repo, RepoMetadataCollectionType.DATA_REPO, data_file='/tmp/test.xlsx')

        shutil.rmtree(tempdir)

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
