""" Installation utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import unittest

from wc_utils.util.installation import parse_requirements


class TestInstallation(unittest.TestCase):

    def testInstallation(self):
        requirements_lines = [
            'numpy\n',
            'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils\n',
        ]
        install_requires, dependency_links = parse_requirements(requirements_lines)
        self.assertEqual(install_requires, ['numpy', 'wc_utils'])
        self.assertEqual(dependency_links, ['git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils'])
