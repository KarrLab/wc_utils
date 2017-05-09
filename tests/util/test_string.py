""" String utility tests

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-20
:Copyright: 2017, Karr Lab
:License: MIT
"""

from wc_utils.util import string
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
        self.assertEqual(string.indent_forest(forest, indentation=2), indent_by_2)

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
        self.assertEqual(string.indent_forest(forest2, indentation=3), indent_with_text)

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
            string.delete_trailing_blanks(lines)
            self.assertEqual(lines, correct_list)

    def test_indent_forest_with_trailing_blanks(self):
        test_string1 = 'test_text1\ntest_text2\n\ntest_text4\n   \n'
        test_string2 = 'test_text5\ntest_text6'
        forest = [test_string1, test_string2]
        self.assertEqual(
            string.indent_forest(forest, keep_trailing_blank_lines=True, indentation=0),
            test_string1 + '\n' + test_string2)
        self.assertEqual(
            string.indent_forest(forest, indentation=0),
            test_string1.rstrip() + '\n' + test_string2)

    def test_find_nth(self):
        self.assertEqual(string.find_nth('123', '0', 1), '123'.find('0'))
        self.assertEqual(string.find_nth('123', '1', 1), '123'.find('1'))
        self.assertEqual(string.find_nth('123', '2', 1), '123'.find('2'))
        self.assertEqual(string.find_nth('123', '3', 1), '123'.find('3'))

        self.assertEqual(string.find_nth('123232323', '3', 1), 2)
        self.assertEqual(string.find_nth('123232323', '3', 2), 4)
        self.assertEqual(string.find_nth('123232323', '3', 3), 6)
        self.assertEqual(string.find_nth('123232323', '3', 4), 8)
        self.assertEqual(string.find_nth('123232323', '3', 5), -1)

        self.assertEqual(string.find_nth('123232323', '23', 1), 1)
        self.assertEqual(string.find_nth('123232323', '23', 2), 3)
        self.assertEqual(string.find_nth('123232323', '23', 3), 5)
        self.assertEqual(string.find_nth('123232323', '23', 4), 7)
        self.assertEqual(string.find_nth('123232323', '23', 5), -1)

        self.assertEqual(string.find_nth('123232323', '123', 1), 0)
        self.assertEqual(string.find_nth('123232323', '123', 2), -1)

        self.assertEqual(string.find_nth('123232323', '1234', 1), -1)

    def test_rfind_nth(self):
        self.assertEqual(string.rfind_nth('123', '0', 1), '123'.rfind('0'))
        self.assertEqual(string.rfind_nth('123', '1', 1), '123'.rfind('1'))
        self.assertEqual(string.rfind_nth('123', '2', 1), '123'.rfind('2'))
        self.assertEqual(string.rfind_nth('123', '3', 1), '123'.rfind('3'))

        self.assertEqual(string.rfind_nth('123232323', '3', 1), 8)
        self.assertEqual(string.rfind_nth('123232323', '3', 2), 6)
        self.assertEqual(string.rfind_nth('123232323', '3', 3), 4)
        self.assertEqual(string.rfind_nth('123232323', '3', 4), 2)
        self.assertEqual(string.rfind_nth('123232323', '3', 5), -1)

        self.assertEqual(string.rfind_nth('123232323', '23', 1), 7)
        self.assertEqual(string.rfind_nth('123232323', '23', 2), 5)
        self.assertEqual(string.rfind_nth('123232323', '23', 3), 3)
        self.assertEqual(string.rfind_nth('123232323', '23', 4), 1)
        self.assertEqual(string.rfind_nth('123232323', '23', 5), -1)

        self.assertEqual(string.rfind_nth('123232323', '123', 1), 0)
        self.assertEqual(string.rfind_nth('123232323', '123', 2), -1)

        self.assertEqual(string.rfind_nth('123232323', '1234', 1), -1)

    def test_partition_nth(self):
        self.assertEqual(string.partition_nth('123', '0', 1), '123'.partition('0'))
        self.assertEqual(string.partition_nth('123', '1', 1), '123'.partition('1'))
        self.assertEqual(string.partition_nth('123', '2', 1), '123'.partition('2'))
        self.assertEqual(string.partition_nth('123', '3', 1), '123'.partition('3'))

        self.assertEqual(string.partition_nth('123232323', '3', 1), ('12', '3', '232323'))
        self.assertEqual(string.partition_nth('123232323', '3', 2), ('1232', '3', '2323'))
        self.assertEqual(string.partition_nth('123232323', '3', 3), ('123232', '3', '23'))
        self.assertEqual(string.partition_nth('123232323', '3', 4), ('12323232', '3', ''))
        self.assertEqual(string.partition_nth('123232323', '3', 5), ('123232323', '', ''))

        self.assertEqual(string.partition_nth('123232323', '23', 1), ('1', '23', '232323'))
        self.assertEqual(string.partition_nth('123232323', '23', 2), ('123', '23', '2323'))
        self.assertEqual(string.partition_nth('123232323', '23', 3), ('12323', '23', '23'))
        self.assertEqual(string.partition_nth('123232323', '23', 4), ('1232323', '23', ''))
        self.assertEqual(string.partition_nth('123232323', '23', 5), ('123232323', '', ''))

        self.assertEqual(string.partition_nth('123232323', '123', 1), ('', '123', '232323'))
        self.assertEqual(string.partition_nth('123232323', '123', 2), ('123232323', '', ''))

        self.assertEqual(string.partition_nth('123232323', '1234', 1), ('123232323', '', ''))

    def test_rpartition_nth(self):
        self.assertEqual(string.rpartition_nth('123', '0', 1), '123'.rpartition('0'))
        self.assertEqual(string.rpartition_nth('123', '1', 1), '123'.rpartition('1'))
        self.assertEqual(string.rpartition_nth('123', '2', 1), '123'.rpartition('2'))
        self.assertEqual(string.rpartition_nth('123', '3', 1), '123'.rpartition('3'))

        self.assertEqual(string.rpartition_nth('123232323', '3', 4), ('12', '3', '232323'))
        self.assertEqual(string.rpartition_nth('123232323', '3', 3), ('1232', '3', '2323'))
        self.assertEqual(string.rpartition_nth('123232323', '3', 2), ('123232', '3', '23'))
        self.assertEqual(string.rpartition_nth('123232323', '3', 1), ('12323232', '3', ''))
        self.assertEqual(string.rpartition_nth('123232323', '3', 5), ('', '', '123232323'))

        self.assertEqual(string.rpartition_nth('123232323', '23', 4), ('1', '23', '232323'))
        self.assertEqual(string.rpartition_nth('123232323', '23', 3), ('123', '23', '2323'))
        self.assertEqual(string.rpartition_nth('123232323', '23', 2), ('12323', '23', '23'))
        self.assertEqual(string.rpartition_nth('123232323', '23', 1), ('1232323', '23', ''))
        self.assertEqual(string.rpartition_nth('123232323', '23', 5), ('', '', '123232323'))

        self.assertEqual(string.rpartition_nth('123232323', '123', 1), ('', '123', '232323'))
        self.assertEqual(string.rpartition_nth('123232323', '123', 2), ('', '', '123232323'))

        self.assertEqual(string.rpartition_nth('123232323', '1234', 1), ('', '', '123232323'))
