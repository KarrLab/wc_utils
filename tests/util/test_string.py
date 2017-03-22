""" String utility tests

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-20
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils.util.string import indent_forest, delete_trailing_blanks
import unittest


class TestStringUtils(unittest.TestCase):

    def test_indent_forest(self):
        forest = [
            '0,1',
            ['1,1', '1,2', ],
            '0,2',
            ['1,2',
             ['2,1', '2,2', ],
             '1,3', ]
        ]
        indent_by_2 = """0,1
  1,1
  1,2
0,2
  1,2
    2,1
    2,2
  1,3"""
        self.assertEqual(indent_forest(forest, indentation=2), indent_by_2)

        forest2 = [
            '0,1',
            ["e e cummings\ncould write\n   but couldn't code"],
            '0,2',
        ]
        indent_with_text = """0,1
   e e cummings
   could write
      but couldn't code
0,2"""
        self.assertEqual(indent_forest(forest2, indentation=3), indent_with_text)

    def test_delete_trailing_blanks(self):
        test_strings = ['test_text\ntest_text',
                        'test_text\ntest_text\n',
                        'test_text\ntest_text\n  \n',
                        'test_text\n\ntest_text\n  \n']
        correct_lists = [
            ['test_text', 'test_text'],
            ['test_text', 'test_text'],
            ['test_text', 'test_text'],
            ['test_text', '', 'test_text']
        ]
        for test_string, correct_list in zip(test_strings, correct_lists):
            lines = test_string.split('\n')
            delete_trailing_blanks(lines)
            self.assertEqual(lines, correct_list)

    def test_indent_forest_with_trailing_blanks(self):
        test_string1 = 'test_text1\ntest_text2\n\ntest_text4\n   \n'
        test_string2 = 'test_text5\ntest_text6'
        forest = [test_string1, test_string2]
        self.assertEqual(
            indent_forest(forest, keep_trailing_blank_lines=True, indentation=0),
            test_string1 + '\n' + test_string2)
        self.assertEqual(
            indent_forest(forest, indentation=0),
            test_string1.rstrip() + '\n' + test_string2)
