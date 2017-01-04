""" Test Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from os import path
from shutil import rmtree
from six import integer_types, string_types
from tempfile import mkdtemp
from wc_utils.workbook import io
from wc_utils.workbook.core import Workbook, Worksheet, Row
import unittest


class TestIo(unittest.TestCase):

    def setUp(self):
        # test data set
        wk = self.wk = Workbook()

        ws0 = wk['Ws-0'] = Worksheet()
        ws0.append(Row(['Id', 'Val-1', 'Val-2', 'Val-3']))
        ws0.append(Row(['a0\taa0\naaa0', 1, 2., True]))
        ws0.append(Row([u'b0\u20ac', 3, 4., False]))
        ws0.append(Row(['c0', 5, 6., None]))

        ws1 = wk['Ws-1'] = Worksheet()
        ws1.append(Row(['Id', 'Val-1', 'Val-2']))
        ws1.append(Row(['a1', 1, 2.]))
        ws1.append(Row(['b1', 3, 4.]))
        ws1.append(Row(['c1', 5, 6.]))

        ws2 = wk['Ws-2'] = Worksheet()
        ws2.append(Row(['Id', 'Val-1', 'Val-2']))
        ws2.append(Row(['a2', 1, 2.]))
        ws2.append(Row(['b2', 3, 4.]))
        ws2.append(Row(['c2', 5, 6.]))

        # create temp directory
        self.tempdir = mkdtemp()

    def tearDown(self):
        # remove temp directory
        rmtree(self.tempdir)

    def test_exceptions_excel(self):
        filename = path.join(self.tempdir, 'test.foo')
        with self.assertRaises(ValueError) as context:
            io.ExcelWriter(filename)
        self.assertIn("Extension of path", str(context.exception))
        self.assertIn("must be '.xlsx'", str(context.exception))

        with self.assertRaises(ValueError) as context:
            io.ExcelReader(filename)
        self.assertIn("Extension of path", str(context.exception))
        self.assertIn("must be '.xlsx'", str(context.exception))

    def test_read_write_excel(self):
        # write to file
        filename = path.join(self.tempdir, 'test.xlsx')
        io.ExcelWriter(filename).run(self.wk)
        self.assertTrue(path.isfile(filename))

        # write to file with style
        style = io.WorkbookStyle()
        style['Ws-0'] = io.WorksheetStyle(head_rows=1, head_columns=1,
                                          head_row_font_bold=True, head_row_fill_fgcolor='CCCCCC', row_height=15)
        io.ExcelWriter(filename).run(self.wk, style=style)
        self.assertTrue(path.isfile(filename))

        # read from file
        wk = io.ExcelReader(filename).run()

        # assert content is the same
        ws = wk['Ws-0']
        self.assertIsInstance(ws[1][0], string_types)
        self.assertIsInstance(ws[1][1], integer_types)
        self.assertIsInstance(ws[1][2], integer_types)
        self.assertIsInstance(ws[1][3], bool)
        self.assertEqual(ws[2][0], u'b0\u20ac')
        self.assertEqual(ws[3][3], None)

        self.assertEqual(wk, self.wk)

    def test_exceptions_csv(self):
        for method in [io.SeparatedValuesWriter, io.SeparatedValuesReader]:
            filename = path.join(self.tempdir, 'test.foo')
            with self.assertRaises(ValueError) as context:
                method(filename)
            self.assertIn("Extension of path", str(context.exception))
            self.assertIn("must be one of '.csv' or '.tsv'", str(context.exception))

            filename = path.join(self.tempdir, '*', 'test.csv')
            with self.assertRaises(ValueError) as context:
                method(filename)
            self.assertIn("cannot have glob pattern '*' in its directory name", str(context.exception))

            filename = path.join(self.tempdir, 'test**.csv')
            with self.assertRaises(ValueError) as context:
                method(filename)
            self.assertIn("must have one glob pattern '*' in its base name", str(context.exception))

    def test_read_write_csv(self):
        # write to files
        filename_pattern = path.join(self.tempdir, 'test-*.csv')
        io.SeparatedValuesWriter(filename_pattern).run(self.wk)
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = io.SeparatedValuesReader(filename_pattern).run()

        # assert content is the same
        ws = wk['Ws-0']
        self.assertIsInstance(ws[1][0], string_types)
        self.assertIsInstance(ws[1][1], integer_types)
        self.assertIsInstance(ws[1][2], float)
        self.assertIsInstance(ws[1][3], bool)
        self.assertEqual(ws[2][0], u'b0\u20ac')
        self.assertEqual(ws[3][3], None)

        self.assertEqual(wk, self.wk)

    def test_read_write_tsv(self):
        # write to files
        filename_pattern = path.join(self.tempdir, 'test-*.tsv')
        io.SeparatedValuesWriter(filename_pattern).run(self.wk)
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = io.SeparatedValuesReader(filename_pattern).run()

        # assert content is the same
        ws = wk['Ws-0']
        self.assertIsInstance(ws[1][0], string_types)
        self.assertIsInstance(ws[1][1], integer_types)
        self.assertIsInstance(ws[1][2], float)
        self.assertIsInstance(ws[1][3], bool)
        self.assertEqual(ws[2][0], u'b0\u20ac')
        self.assertEqual(ws[3][3], None)

        self.assertEqual(wk, self.wk)

    def test_write_read(self):
        file = path.join(self.tempdir, 'test.xlsx')
        io.write(file, self.wk)
        wk = io.read(file)
        self.assertEqual(wk, self.wk)

        file = path.join(self.tempdir, 'test-*.csv')
        io.write(file, self.wk)
        wk = io.read(file)
        self.assertEqual(wk, self.wk)

    def test_convert(self):
        source = path.join(self.tempdir, 'test.xlsx')
        io.ExcelWriter(source).run(self.wk)

        # copy excel->sv
        dest = path.join(self.tempdir, 'test-*.csv')
        io.convert(source, dest)
        wk = io.SeparatedValuesReader(dest).run()
        self.assertEqual(wk, self.wk)

        # copy sv->excel
        source = path.join(self.tempdir, 'test-*.csv')
        dest = path.join(self.tempdir, 'test2.xlsx')
        io.convert(source, dest)
        wk = io.ExcelReader(dest).run()
        self.assertEqual(wk, self.wk)

        # copy same format - excel
        source = path.join(self.tempdir, 'test.xlsx')
        dest = path.join(self.tempdir, 'test3.xlsx')
        io.convert(source, dest)
        wk = io.ExcelReader(dest).run()
        self.assertEqual(wk, self.wk)

        # copy same format - csv
        source = path.join(self.tempdir, 'test-*.csv')
        dest = path.join(self.tempdir, 'test2-*.csv')
        io.convert(source, dest)
        wk = io.SeparatedValuesReader(dest).run()
        self.assertEqual(wk, self.wk)

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
        io.ExcelWriter(filename_excel).run(self.wk)

        filename_pattern_separated_values = path.join(self.tempdir, 'test-*.csv')
        io.convert(filename_excel, filename_pattern_separated_values)
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-0')))
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-1')))
        self.assertTrue(path.isfile(filename_pattern_separated_values.replace('*', '{}').format('Ws-2')))

        # read from files
        wk = io.SeparatedValuesReader(filename_pattern_separated_values).run()

        # assert content is the same
        self.assertEqual(wk, self.wk)

    def test_convert_csv_to_excel(self):
        filename_pattern_separated_values = path.join(self.tempdir, 'test-*.csv')
        io.SeparatedValuesWriter(filename_pattern_separated_values).run(self.wk)

        filename_excel = path.join(self.tempdir, 'test.xlsx')
        io.convert(filename_pattern_separated_values, filename_excel)
        self.assertTrue(path.isfile(filename_excel))

        # read from files
        wk = io.ExcelReader(filename_excel).run()

        # assert content is the same
        self.assertEqual(wk, self.wk)
