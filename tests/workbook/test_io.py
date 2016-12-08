""" Test Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from os import path
from shutil import rmtree
from six import integer_types, string_types
from tempfile import mkdtemp
from wc_utils.workbook import io
from wc_utils.workbook.core import Workbook, Worksheet, Row, Cell
from wc_utils.util.types import assert_value_equal
import unittest


class TestCore(unittest.TestCase):

    def setUp(self):
        # test data set
        wk = self.wk = Workbook()

        ws0 = wk.worksheets['Ws-0'] = Worksheet()
        ws0.rows.append(Row([Cell('Id'), Cell('Val-1'), Cell('Val-2'), Cell('Val-3')]))
        ws0.rows.append(Row([Cell('a0\taa0\naaa0'), Cell(1), Cell(2.), Cell(True)]))
        ws0.rows.append(Row([Cell(u'b0\u20ac'), Cell(3), Cell(4.), Cell(False)]))
        ws0.rows.append(Row([Cell('c0'), Cell(5), Cell(6.), Cell(None)]))

        ws1 = wk.worksheets['Ws-1'] = Worksheet()
        ws1.rows.append(Row([Cell('Id'), Cell('Val-1'), Cell('Val-2')]))
        ws1.rows.append(Row([Cell('a1'), Cell(1), Cell(2.)]))
        ws1.rows.append(Row([Cell('b1'), Cell(3), Cell(4.)]))
        ws1.rows.append(Row([Cell('c1'), Cell(5), Cell(6.)]))

        ws2 = wk.worksheets['Ws-2'] = Worksheet()
        ws2.rows.append(Row([Cell('Id'), Cell('Val-1'), Cell('Val-2')]))
        ws2.rows.append(Row([Cell('a2'), Cell(1), Cell(2.)]))
        ws2.rows.append(Row([Cell('b2'), Cell(3), Cell(4.)]))
        ws2.rows.append(Row([Cell('c2'), Cell(5), Cell(6.)]))

        # create temp directory
        self.tempdir = mkdtemp()

    def tearDown(self):
        # remove temp directory
        rmtree(self.tempdir)

    def test_read_write_excel(self):
        # write to file
        filename = path.join(self.tempdir, 'test.xlsx')
        io.write_excel(filename, self.wk)
        self.assertTrue(path.isfile(filename))

        # write to file with style
        style = io.WorkbookStyle()
        style.worksheets['Ws-0'] = io.WorksheetStyle(head_rows=1, head_columns=1,
                                                     head_row_font_bold=True, head_row_fill_fgcolor='CCCCCC', row_height=15)
        io.write_excel(filename, self.wk, style=style)
        self.assertTrue(path.isfile(filename))

        # read from file
        wk = io.read_excel(filename)

        # assert content is the same
        ws = wk.worksheets['Ws-0']
        self.assertIsInstance(ws.rows[1].cells[0].value, string_types)
        self.assertIsInstance(ws.rows[1].cells[1].value, integer_types)
        self.assertIsInstance(ws.rows[1].cells[2].value, integer_types)
        self.assertIsInstance(ws.rows[1].cells[3].value, bool)
        self.assertEqual(ws.rows[2].cells[0].value, u'b0\u20ac')
        self.assertEqual(ws.rows[3].cells[3].value, None)

        assert_value_equal(wk, self.wk)

    def test_read_write_csv(self):
        # write to files
        filename_pattern = path.join(self.tempdir, 'test-*.csv')
        io.write_separated_values(filename_pattern, self.wk)
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = io.read_separated_values(filename_pattern)

        # assert content is the same
        ws = wk.worksheets['Ws-0']
        self.assertIsInstance(ws.rows[1].cells[0].value, string_types)
        self.assertIsInstance(ws.rows[1].cells[1].value, integer_types)
        self.assertIsInstance(ws.rows[1].cells[2].value, float)
        self.assertIsInstance(ws.rows[1].cells[3].value, bool)
        self.assertEqual(ws.rows[2].cells[0].value, u'b0\u20ac')
        self.assertEqual(ws.rows[3].cells[3].value, None)

        assert_value_equal(wk, self.wk)

    def test_read_write_tsv(self):
        # write to files
        filename_pattern = path.join(self.tempdir, 'test-*.tsv')
        io.write_separated_values(filename_pattern, self.wk)
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = io.read_separated_values(filename_pattern)

        # assert content is the same
        ws = wk.worksheets['Ws-0']
        self.assertIsInstance(ws.rows[1].cells[0].value, string_types)
        self.assertIsInstance(ws.rows[1].cells[1].value, integer_types)
        self.assertIsInstance(ws.rows[1].cells[2].value, float)
        self.assertIsInstance(ws.rows[1].cells[3].value, bool)
        self.assertEqual(ws.rows[2].cells[0].value, u'b0\u20ac')
        self.assertEqual(ws.rows[3].cells[3].value, None)

        assert_value_equal(wk, self.wk)

    def test_write_read(self):
        file = path.join(self.tempdir, 'test.xlsx')
        io.write(file, self.wk)
        wk = io.read(file)
        assert_value_equal(wk, self.wk)

        file = path.join(self.tempdir, 'test-*.csv')
        io.write(file, self.wk)
        wk = io.read(file)
        assert_value_equal(wk, self.wk)

    def test_convert(self):
        source = path.join(self.tempdir, 'test.xlsx')
        io.write_excel(source, self.wk)

        # copy excel->sv
        dest = path.join(self.tempdir, 'test-*.csv')
        io.convert(source, dest)
        wk = io.read_separated_values(dest)
        assert_value_equal(wk, self.wk)

        # copy sv->excel
        source = path.join(self.tempdir, 'test-*.csv')
        dest = path.join(self.tempdir, 'test2.xlsx')
        io.convert(source, dest)
        wk = io.read_excel(dest)
        assert_value_equal(wk, self.wk)

        # copy same format - excel
        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test3.xlsx')
        io.convert(source, dest)
        wk = io.read_excel(dest)
        assert_value_equal(wk, self.wk)

        # copy same format - csv
        source = path.join(self.tempdir, 'test-*.csv')
        dest = path.join(self.tempdir, 'test2-*.csv')
        io.convert(source, dest)
        wk = io.read_separated_values(dest)
        assert_value_equal(wk, self.wk)

        # negative examples
        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test.xlsx')
        self.assertRaises(ValueError, lambda: io.convert(source, dest))

        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test.xlsx2')
        self.assertRaises(ValueError, lambda: io.convert(source, dest))

        source = path.join(self.tempdir, 'test.xlsx2')
        dest = path.join(self.tempdir, 'test.xlsx')
        self.assertRaises(ValueError, lambda: io.convert(source, dest))

    def test_convert_excel_to_csv(self):
        filename_excel = path.join(self.tempdir, 'test.xlsx')
        io.write_excel(filename_excel, self.wk)

        filename_pattern_separated_values = path.join(self.tempdir, 'test-*.csv')
        io.convert_excel_to_separated_values(filename_excel, filename_pattern_separated_values)
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = io.read_separated_values(filename_pattern_separated_values)

        # assert content is the same
        assert_value_equal(wk, self.wk)

    def test_convert_csv_to_excel(self):
        filename_pattern_separated_values = path.join(self.tempdir, 'test-*.csv')
        io.write_separated_values(filename_pattern_separated_values, self.wk)

        filename_excel = path.join(self.tempdir, 'test.xlsx')
        io.convert_separated_values_to_excel(filename_pattern_separated_values, filename_excel)
        self.assertTrue(path.isfile(filename_excel))

        # read from files
        wk = io.read_excel(filename_excel)

        # assert content is the same
        assert_value_equal(wk, self.wk)
