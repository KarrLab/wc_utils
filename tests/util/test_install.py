""" Installation utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import unittest

from wc_utils.util.install import parse_requirements


class TestInstall(unittest.TestCase):

    def test_install(self):
        requirements_lines = [
            'numpy  \n',
            'scipy>=1.0.1\n',
            'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils\n',
            'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils \n',
            'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils #comment\n',
            'git+git://github.com/KarrLab/wc_lang.git#egg=wc_lang==0.0.1 #comment\n',
            'git+git://github.com/KarrLab/wc_lang.git#egg=wc_lang<0.0.5 \n',
        ]
        install_requires, dependency_links = parse_requirements(requirements_lines)
        self.assertEqual(sorted(install_requires), [
            'numpy', 'scipy>=1.0.1', 'wc_lang<0.0.5', 'wc_lang==0.0.1', 'wc_utils'
            ])
        self.assertEqual(sorted(dependency_links), [
            'git+git://github.com/KarrLab/wc_lang.git#egg=wc_lang',
            'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils',
            ])
