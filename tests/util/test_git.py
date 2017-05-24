""" Test of Git utilities

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2017-05-24
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils.util import git
import unittest


class TestGit(unittest.TestCase):

    def test(self):
        md = git.get_repo_metadata(dirname='.')
        self.assertIn(md.url, ['https://github.com/KarrLab/wc_utils.git', 'git@github.com:KarrLab/wc_utils.git'])
        self.assertEqual(md.branch, 'master')
