""" Installation utilities tests.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-06-21
:Copyright: 2016-2017, Karr Lab
:License: MIT
"""

import unittest

from wc_utils.util.install import parse_requirements


class TestInstall(unittest.TestCase):

    def test_install(self):
        requirements_lines = [
            'coverage<4.4\n',
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
            'coverage<4.4', 'numpy', 'scipy>=1.0.1', 'wc_lang<0.0.5', 'wc_lang==0.0.1', 'wc_utils'
            ])
        self.assertEqual(sorted(dependency_links), [
            'git+git://github.com/KarrLab/wc_lang.git#egg=wc_lang',
            'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils',
            ])
