""" Test Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from copy import deepcopy
from wc_utils.workbook.core import Workbook, Worksheet, Row, WorksheetDifference, RowDifference, CellDifference
import unittest


class TestCore(unittest.TestCase):

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

    def test_eq(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk == wk, True)

        wk = deepcopy(self.wk)
        wk['Ws-3'] = Worksheet()
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk['Ws-2'].append(Row())
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk['Ws-2'][0].append(None)
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk['Ws-1'][1][2] = 3.5
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk['Ws-1'][1][2] = 'test'
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

    def test_ne(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk != wk, False)

        wk = deepcopy(self.wk)
        wk['Ws-3'] = Worksheet()
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk['Ws-2'].append(Row())
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk['Ws-2'][0].append(None)
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk['Ws-1'][1][2] = 3.5
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

        wk = deepcopy(self.wk)
        wk['Ws-1'][1][2] = 'test'
        self.assertEqual(self.wk != wk, True)
        self.assertEqual(wk != self.wk, True)

    def test_difference(self):
        wk = deepcopy(self.wk)
        self.assertEqual(self.wk.difference(wk), {})

        wk = deepcopy(self.wk)
        wk['Ws-3'] = Worksheet()
        self.assertEqual(self.wk.difference(wk), {'Ws-3': 'Sheet not in self'})
        self.assertEqual(wk.difference(self.wk), {'Ws-3': 'Sheet not in other'})

        wk = deepcopy(self.wk)
        wk['Ws-2'].append(Row())
        self.assertEqual(self.wk.difference(wk), {'Ws-2': WorksheetDifference({4: 'Row not in self'})})
        self.assertEqual(wk.difference(self.wk), {'Ws-2': WorksheetDifference({4: 'Row not in other'})})

        wk = deepcopy(self.wk)
        wk['Ws-2'][0].append(None)
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-2': WorksheetDifference({0: RowDifference({3: 'Cell not in self'})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-2': WorksheetDifference({0: RowDifference({3: 'Cell not in other'})})})

        wk = deepcopy(self.wk)
        wk['Ws-1'][1][2] = 3.5
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('2.0 != 3.5')})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('3.5 != 2.0')})})})

        wk = deepcopy(self.wk)
        wk['Ws-1'][1][2] = 'test'
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('2.0 != test')})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-1': WorksheetDifference({1: RowDifference({2: CellDifference('test != 2.0')})})})
