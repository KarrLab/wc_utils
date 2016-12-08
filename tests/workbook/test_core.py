""" Test Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from wc_utils.workbook.core import Workbook, Worksheet, Row, Cell, WorksheetDifference, RowDifference, CellDifference
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

    def test_eq(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk == wk, True)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-3'] = Worksheet()
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows.append(Row())
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows[0].cells.append(Cell())
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 3.5
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 'test'
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

    def test_ne(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk != wk, False)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-3'] = Worksheet()
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows.append(Row())
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows[0].cells.append(Cell())
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 3.5
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 'test'
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

    def test_difference(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk.difference(wk), {})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-3'] = Worksheet()
        self.assertEqual(self.wk.difference(wk), {'Ws-3': 'Sheet not in self'})
        self.assertEqual(wk.difference(self.wk), {'Ws-3': 'Sheet not in other'})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows.append(Row())
        self.assertEqual(self.wk.difference(wk), {'Ws-2': WorksheetDifference({4: 'Row not in self'})})
        self.assertEqual(wk.difference(self.wk), {'Ws-2': WorksheetDifference({4: 'Row not in other'})})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-2'].rows[0].cells.append(Cell())
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-2': WorksheetDifference({0: RowDifference({3: 'Cell not in self'})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-2': WorksheetDifference({0: RowDifference({3: 'Cell not in other'})})})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 3.5
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('2.0 != 3.5')})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('3.5 != 2.0')})})})

        wk = deepcopy(self.wk)
        wk.worksheets['Ws-1'].rows[1].cells[2].value = 'test'
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('class: float != class: str')})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('class: str != class: float')})})})
