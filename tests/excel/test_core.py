""" Test Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from collections import OrderedDict
from copy import deepcopy
from os import path
from wc_utils.excel import core
from wc_utils.util.types import assert_value_equal
import shutil
import six
import tempfile
import unittest


class TestExcel(unittest.TestCase):

    def setUp(self):
        # test data set
        wk = self.wk = core.Workbook()

        ws0 = wk.worksheets['Ws-0'] = core.Worksheet()
        ws0.rows.append(core.Row([core.Cell('Id'), core.Cell('Val-1'), core.Cell('Val-2'), core.Cell('Val-3')]))
        ws0.rows.append(core.Row([core.Cell('a0\taa0\naaa0'), core.Cell(1), core.Cell(2.), core.Cell(True)]))
        ws0.rows.append(core.Row([core.Cell(u'b0\u20ac'), core.Cell(3), core.Cell(4.), core.Cell(False)]))
        ws0.rows.append(core.Row([core.Cell('c0'), core.Cell(5), core.Cell(6.), core.Cell(None)]))

        ws1 = wk.worksheets['Ws-1'] = core.Worksheet()
        ws1.rows.append(core.Row([core.Cell('Id'), core.Cell('Val-1'), core.Cell('Val-2')]))
        ws1.rows.append(core.Row([core.Cell('a1'), core.Cell(1), core.Cell(2.)]))
        ws1.rows.append(core.Row([core.Cell('b1'), core.Cell(3), core.Cell(4.)]))
        ws1.rows.append(core.Row([core.Cell('c1'), core.Cell(5), core.Cell(6.)]))

        ws2 = wk.worksheets['Ws-2'] = core.Worksheet()
        ws2.rows.append(core.Row([core.Cell('Id'), core.Cell('Val-1'), core.Cell('Val-2')]))
        ws2.rows.append(core.Row([core.Cell('a2'), core.Cell(1), core.Cell(2.)]))
        ws2.rows.append(core.Row([core.Cell('b2'), core.Cell(3), core.Cell(4.)]))
        ws2.rows.append(core.Row([core.Cell('c2'), core.Cell(5), core.Cell(6.)]))

        # create temp directory
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        # remove temp directory
        shutil.rmtree(self.tempdir)

    def test_read_write_excel(self):
        # write to file
        filename = path.join(self.tempdir, 'test.xlsx')
        core.write_excel(filename, self.wk)
        self.assertTrue(path.isfile(filename))

        # write to file with style
        style = core.WorkbookStyle()
        style.worksheets['Ws-0'] = core.WorksheetStyle(head_rows=1, head_columns=1,
                                                       head_row_font_bold=True, head_row_fill_fgcolor='CCCCCC', row_height=15)
        core.write_excel(filename, self.wk, style)
        self.assertTrue(path.isfile(filename))

        # read from file
        wk = core.read_excel(filename)

        # assert content is the same
        ws = wk.worksheets['Ws-0']
        self.assertIsInstance(ws.rows[1].cells[0].value, six.string_types)
        self.assertIsInstance(ws.rows[1].cells[1].value, six.integer_types)
        self.assertIsInstance(ws.rows[1].cells[2].value, six.integer_types)
        self.assertIsInstance(ws.rows[1].cells[3].value, bool)
        self.assertEqual(ws.rows[2].cells[0].value, u'b0\u20ac')
        self.assertEqual(ws.rows[3].cells[3].value, None)

        assert_value_equal(wk, self.wk)

    def test_read_write_csv(self):
        # write to files
        filename_pattern = path.join(self.tempdir, 'test-*.csv')
        core.write_separated_values(filename_pattern, self.wk)
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = core.read_separated_values(filename_pattern)

        # assert content is the same
        ws = wk.worksheets['Ws-0']
        self.assertIsInstance(ws.rows[1].cells[0].value, six.string_types)
        self.assertIsInstance(ws.rows[1].cells[1].value, six.integer_types)
        self.assertIsInstance(ws.rows[1].cells[2].value, float)
        self.assertIsInstance(ws.rows[1].cells[3].value, bool)
        self.assertEqual(ws.rows[2].cells[0].value, u'b0\u20ac')
        self.assertEqual(ws.rows[3].cells[3].value, None)

        assert_value_equal(wk, self.wk)

    def test_read_write_tsv(self):
        # write to files
        filename_pattern = path.join(self.tempdir, 'test-*.tsv')
        core.write_separated_values(filename_pattern, self.wk)
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = core.read_separated_values(filename_pattern)

        # assert content is the same
        ws = wk.worksheets['Ws-0']
        self.assertIsInstance(ws.rows[1].cells[0].value, six.string_types)
        self.assertIsInstance(ws.rows[1].cells[1].value, six.integer_types)
        self.assertIsInstance(ws.rows[1].cells[2].value, float)
        self.assertIsInstance(ws.rows[1].cells[3].value, bool)
        self.assertEqual(ws.rows[2].cells[0].value, u'b0\u20ac')
        self.assertEqual(ws.rows[3].cells[3].value, None)

        assert_value_equal(wk, self.wk)

    def test_write_read(self):
        file = path.join(self.tempdir, 'test.xlsx')
        core.write(file, self.wk)
        wk = core.read(file)
        assert_value_equal(wk, self.wk)

        file = path.join(self.tempdir, 'test-*.csv')
        core.write(file, self.wk)
        wk = core.read(file)
        assert_value_equal(wk, self.wk)

    def test_convert(self):
        source = path.join(self.tempdir, 'test.xlsx')
        core.write_excel(source, self.wk)

        # copy excel->sv
        dest = path.join(self.tempdir, 'test-*.csv')
        core.convert(source, dest)
        wk = core.read_separated_values(dest)
        assert_value_equal(wk, self.wk)

        # copy sv->excel
        source = path.join(self.tempdir, 'test-*.csv')
        dest = path.join(self.tempdir, 'test2.xlsx')
        core.convert(source, dest)
        wk = core.read_excel(dest)
        assert_value_equal(wk, self.wk)

        # copy same format - excel
        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test3.xlsx')
        core.convert(source, dest)
        wk = core.read_excel(dest)
        assert_value_equal(wk, self.wk)

        # copy same format - csv
        source = path.join(self.tempdir, 'test-*.csv')
        dest = path.join(self.tempdir, 'test2-*.csv')
        core.convert(source, dest)
        wk = core.read_separated_values(dest)
        assert_value_equal(wk, self.wk)

        # negative examples
        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test.xlsx')
        self.assertRaises(ValueError, lambda: core.convert(source, dest))

        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test.xlsx2')
        self.assertRaises(ValueError, lambda: core.convert(source, dest))

        source = path.join(self.tempdir, 'test.xlsx2')
        dest = path.join(self.tempdir, 'test.xlsx')
        self.assertRaises(ValueError, lambda: core.convert(source, dest))

    def test_convert_excel_to_csv(self):
        filename_excel = path.join(self.tempdir, 'test.xlsx')
        core.write_excel(filename_excel, self.wk)

        filename_pattern_separated_values = path.join(self.tempdir, 'test-*.csv')
        core.convert_excel_to_separated_values(filename_excel, filename_pattern_separated_values)
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = core.read_separated_values(filename_pattern_separated_values)

        # assert content is the same
        assert_value_equal(wk, self.wk)

    def test_convert_csv_to_excel(self):
        filename_pattern_separated_values = path.join(self.tempdir, 'test-*.csv')
        core.write_separated_values(filename_pattern_separated_values, self.wk)

        filename_excel = path.join(self.tempdir, 'test.xlsx')
        core.convert_separated_values_to_excel(filename_pattern_separated_values, filename_excel)
        self.assertTrue(path.isfile(filename_excel))

        # read from files
        wk = core.read_excel(filename_excel)

        # assert content is the same
        assert_value_equal(wk, self.wk)

    def test_difference(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk.difference(wk), {})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-3'] = core.Worksheet()
        self.assertEqual(self.wk.difference(wk), {'Ws-3': 'Sheet not in self'})
        self.assertEqual(wk.difference(self.wk), {'Ws-3': 'Sheet not in other'})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows.append(core.Row())
        self.assertEqual(self.wk.difference(wk), {'Ws-2': core.WorksheetDifference({4: 'Row not in self'})})
        self.assertEqual(wk.difference(self.wk), {'Ws-2': core.WorksheetDifference({4: 'Row not in other'})})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows[0].cells.append(core.Cell())
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-2': core.WorksheetDifference({0: core.RowDifference({3: 'Cell not in self'})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-2': core.WorksheetDifference({0: core.RowDifference({3: 'Cell not in other'})})})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 3.5
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-1': core.WorksheetDifference({1: core.RowDifference({2: core.CellDifference('2.0 != 3.5')})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-1': core.WorksheetDifference({1: core.RowDifference({2: core.CellDifference('3.5 != 2.0')})})})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 'test'
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-1': core.WorksheetDifference({1: core.RowDifference({2: core.CellDifference('class: float != class: str')})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-1': core.WorksheetDifference({1: core.RowDifference({2: core.CellDifference('class: str != class: float')})})})
