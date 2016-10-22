""" Installation utilities.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import unittest

from wc_utils.util.installation import install_packages

class TestInstallation(unittest.TestCase):

    def testInstallation(self):
        requirements_lines = ['numpy\n',
        'git+git://github.com/KarrLab/wc_utils.git#egg=wc_utils\n']
        self.assertEqual( install_packages( requirements_lines ), ['numpy', 'wc_utils'] )
