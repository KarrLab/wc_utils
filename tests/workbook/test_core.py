""" Test Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016-2018, Karr Lab
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

    def test_init(self):
        self.assertEqual(
            Worksheet(Row([0, 1, 2])),
            Worksheet(Worksheet(Row([0, 1, 2]))))
        self.assertEqual(
            Row([0, 1, 2]),
            Row(Row([0, 1, 2])))

    def test_getitem(self):
        ws = self.wk['Ws-0']
        self.assertEqual(ws[0], Row(['Id', 'Val-1', 'Val-2', 'Val-3']))
        self.assertEqual(ws[0:1], Worksheet([Row(['Id', 'Val-1', 'Val-2', 'Val-3'])]))
        self.assertEqual(ws[1:3], Worksheet([
            Row(['a0\taa0\naaa0', 1, 2., True]),
            Row([u'b0\u20ac', 3, 4., False]),        
        ]))

        self.assertEqual(ws[0][1], 'Val-1')
        self.assertEqual(ws[0][2:4], Row(['Val-2', 'Val-3']))

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

        self.assertEqual(self.wk == 'wk', False)
        self.assertEqual(self.wk != 'wk', True)
        self.assertEqual(self.wk['Ws-1'] == 'Ws-1', False)
        self.assertEqual(self.wk['Ws-1'] != 'Ws-1', True)
        self.assertEqual(self.wk['Ws-1'][1] == ['a1', 1, 2.], False)
        self.assertEqual(self.wk['Ws-1'][1] != ['a1', 1, 2.], True)

        wk = deepcopy(self.wk)
        wk['Ws-1'] = 'ws'
        self.assertEqual(self.wk == wk, False)
        self.assertEqual(wk == self.wk, False)

        wk = deepcopy(self.wk)
        wk['Ws-1'][1] = ['a1', 1, 2.]
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
        self.assertEqual(str(self.wk.difference(wk)), '')

        wk = deepcopy(self.wk)
        wk['Ws-3'] = Worksheet()
        self.assertEqual(self.wk.difference(wk), {'Ws-3': 'Sheet not in self'})
        self.assertEqual(wk.difference(self.wk), {'Ws-3': 'Sheet not in other'})
        self.assertEqual(str(wk.difference(self.wk)), 'Sheet Ws-3:\n  Sheet not in other')

        wk = deepcopy(self.wk)
        wk['Ws-2'].append(Row())
        self.assertEqual(self.wk.difference(wk), {'Ws-2': WorksheetDifference({4: 'Row not in self'})})
        self.assertEqual(wk.difference(self.wk), {'Ws-2': WorksheetDifference({4: 'Row not in other'})})
        self.assertEqual(str(wk.difference(self.wk)), 'Sheet Ws-2:\n  Row 5:\n    Row not in other')

        wk = deepcopy(self.wk)
        wk['Ws-2'][0].append(None)
        self.assertEqual(self.wk.difference(wk),
                         {'Ws-2': WorksheetDifference({0: RowDifference({3: 'Cell not in self'})})})
        self.assertEqual(wk.difference(self.wk),
                         {'Ws-2': WorksheetDifference({0: RowDifference({3: 'Cell not in other'})})})
        self.assertEqual(str(wk.difference(self.wk)), 'Sheet Ws-2:\n  Row 1:\n    Cell D: Cell not in other')

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

        with self.assertRaisesRegex(ValueError, '`other` must be an instance of `Workbook`'):
            self.wk.difference('wk')

        wk = deepcopy(self.wk)
        wk['Ws-1'] = 'Ws-1'
        with self.assertRaisesRegex(ValueError, '`other` must be an instance of `Worksheet`'):
            self.wk.difference(wk)

        wk = deepcopy(self.wk)
        wk['Ws-1'][1] = ['a1', 1, 2.]
        with self.assertRaisesRegex(ValueError, '`other` must be an instance of `Row`'):
            self.wk.difference(wk)

    def test_remove_empty_final_rows(self):
        ws = Worksheet()
        ws.append(Row(['a', 'b']))
        ws.append(Row([None, None]))
        ws.append(Row(['c', 'd']))
        ws.append(Row([None, None]))
        ws.append(Row([None, None]))

        self.assertEqual(len(ws), 5)

        ws.remove_empty_final_rows()

        self.assertEqual(len(ws), 3)
        self.assertEqual(list(ws[0]), ['a', 'b'])
        self.assertEqual(list(ws[1]), [None, None])
        self.assertEqual(list(ws[2]), ['c', 'd'])

    def test_remove_empty_final_cols(self):
        ws = Worksheet()
        ws.append(Row(['a', None, None]))
        ws.append(Row(['b', None, 'd', None, '']))

        self.assertEqual(len(ws), 2)

        ws.remove_empty_final_cols()

        self.assertEqual(len(ws), 2)
        self.assertEqual(ws[0], Row(['a', None, None]))
        self.assertEqual(ws[1], Row(['b', None, 'd']))

    def test_remove_empty_final_rows_and_cols(self):
        ws = Worksheet()
        ws.append(Row(['a', None, 'c', None, None]))
        ws.append(Row(['b', None, 'd', '']))
        ws.append(Row([None, None, None, None, None]))
        ws.append(Row([None, None]))

        ws.remove_empty_final_rows()
        ws.remove_empty_final_cols()

        self.assertEqual(len(ws), 2)
        self.assertEqual(ws[0], Row(['a', None, 'c']))
        self.assertEqual(ws[1], Row(['b', None, 'd']))
