""" Test list utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-30
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utils.util.list import transpose
import unittest


class TestTranspose(unittest.TestCase):

    def test_transpose(self):
        lst = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        t_lst = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
        self.assertEqual(transpose(lst), t_lst)
