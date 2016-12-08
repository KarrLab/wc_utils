""" Excel utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-28
:Copyright: 2016, Karr Lab
:License: MIT
"""

from collections import OrderedDict
from openpyxl.utils import get_column_letter


class Workbook(object):
    """ Represents an Excel workbook

    Attributes:
        worksheets (:obj:`OrderedDict`): dictionary of component worksheets
    """

    def __init__(self, worksheets=None):
        """
        Args:
            worksheets (:obj:`OrderedDict`, optional): dictionary of component worksheets
        """
        self.worksheets = worksheets or OrderedDict()

    def __eq__(self, other):
        """ Compare two workbooks

        Args:
            other (:obj:`Workbook`): other workbook

        Returns:
            :obj:`bool`: true if workbooks are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        if set(self.worksheets.keys()) != set(other.worksheets.keys()):
            return False

        for name, sheet in self.worksheets.items():
            if not sheet.__eq__(other.worksheets[name]):
                return False

        return True

    def __ne__(self, other):
        """ Compare two workbooks

        Args:
            other (:obj:`Workbook`): other workbook

        Returns:
            :obj:`bool`: true if workbooks are semantically unequal
        """
        return not self.__eq__(other)

    def difference(self, other):
        """ Get difference with another workbook

        Args:
            other (:obj:`Workbook`): other workbook

        Returns:
            :obj:`dict`: dictionary of differences, grouped by worksheet

        Raises:
            :obj:`ValueError`: if other is not an instance of `workbook`
        """

        if other.__class__ is not self.__class__:
            raise ValueError('`other` must be an instance of `Workbook`')

        diff = WorkbookDifference()
        for name, sheet in self.worksheets.items():
            if name in other.worksheets:
                sheet_diff = sheet.difference(other.worksheets[name])
                if sheet_diff:
                    diff[name] = sheet_diff
            else:
                diff[name] = 'Sheet not in other'

        for name in other.worksheets.keys():
            if name not in self.worksheets:
                diff[name] = 'Sheet not in self'

        return diff


class Worksheet(object):
    """ Represents an Excel worksheet

    Attributes:
        rows (:obj: `list` of `Row`): list of rows
    """

    def __init__(self, rows=None):
        """
        Args:
            rows (:obj:`list` of `Row`, optional): list of rows
        """
        self.rows = rows or []

    def __eq__(self, other):
        """ Compare two worksheets

        Args:
            other (:obj:`Worksheet`): other worksheet

        Returns:
            :obj:`bool`: True if worksheets are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        if len(self.rows) != len(other.rows):
            return False

        for row_self, row_other in zip(self.rows, other.rows):
            if not row_self.__eq__(row_other):
                return False

        return True

    def __ne__(self, other):
        """ Compare two worksheets

        Args:
            other (:obj:`Worksheet`): other worksheet

        Returns:
            :obj:`bool`: True if worksheets are semantically unequal
        """
        return not self.__eq__(other)

    def difference(self, other):
        """ Get difference with another worksheet

        Args:
            other (:obj:`Worksheet`): other worksheet

        Returns:
            :obj:`WorksheeDifference`: dictionary of differences, grouped by row

        Raises:
            :obj:`ValueError`: if other is not an instance of `Worksheet`
        """
        if other.__class__ is not self.__class__:
            raise ValueError('`other` must be an instance of `Worksheet`')

        diff = WorksheetDifference()

        for i_row, row_self in enumerate(self.rows):
            if i_row < len(other.rows):
                diff_row = row_self.difference(other.rows[i_row])
                if diff_row:
                    diff[i_row] = diff_row
            else:
                diff[i_row] = 'Row not in other'

        for i_row in range(len(self.rows), len(other.rows)):
            diff[i_row] = 'Row not in self'

        return diff


class Row(object):
    """ Represents a row of an Excel worksheet

    Attributes:
        cells (:obj: `list` of `Cell`): list of cells
    """

    def __init__(self, cells=None):
        """
        Args:
            cells (:obj:`list` of `Cell`, optional): list of cells
        """
        self.cells = cells or []

    def __eq__(self, other):
        """ Compare rows

        Args:
            other (:obj:`Row`): other row

        Returns:
            :obj:`bool`: True if rows are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        if len(self.cells) != len(other.cells):
            return False

        for cell_self, cell_other in zip(self.cells, other.cells):
            if not cell_self.__eq__(cell_other):
                return False

        return True

    def __ne__(self, other):
        """ Compare rows

        Args:
            other (:obj:`Row`): other row

        Returns:
            :obj:`bool`: True if rows are semantically unequal
        """
        if other.__class__ is not self.__class__:
            return False

    def difference(self, other):
        """ Get difference with another row

        Args:
            other (:obj:`Row`): other row

        Returns:
            :obj:`RowDifference`: dictionary of differences

        Raises:
            :obj:`ValueError`: if other is not an instance of `Row`
        """

        if other.__class__ is not self.__class__:
            raise ValueError('`other` must be an instance of `Row`')

        diff = RowDifference()

        for i_cell, cell_self in enumerate(self.cells):
            if i_cell < len(other.cells):
                diff_cell = cell_self.difference(other.cells[i_cell])
                if diff_cell:
                    diff[i_cell] = diff_cell
            else:
                diff[i_cell] = 'Cell not in other'

        for i_cell in range(len(self.cells), len(other.cells)):
            diff[i_cell] = 'Cell not in self'

        return diff


class Cell(object):
    """ Represents a cell of an Excel worksheet

    Attributes:
        value (:obj: `object`): value
    """

    def __init__(self, value=None):
        """
        Args:
            value (:obj:`object`, optional): value
        """
        self.value = value

    def __eq__(self, other):
        """ Compare cells

        Args:
            other (:obj:`Cell`): other cell

        Returns:
            :obj:`bool`: True if cells are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        return self.value == other.value

    def __ne__(self, other):
        """ Compare cells

        Args:
            other (:obj:`Cell`): other cell

        Returns:
            :obj:`bool`: True if cells are semantically unequal
        """
        return not self.__eq__(other)

    def difference(self, other):
        """ Get difference with another cell

        Args:
            other (:obj:`Cell`): other cell

        Returns:
            :obj:`CellDifference`: difference

        Raises:
            :obj:`ValueError`: if other is not an instance of `Cell`
        """
        if other.__class__ is not self.__class__:
            raise ValueError('`other` must be an instance of `Cell`')

        if self.value == other.value:
            return CellDifference()
        elif self.value.__class__ is not other.value.__class__:
            return CellDifference('class: {} != class: {}'.format(self.value.__class__.__name__, other.value.__class__.__name__))
        else:
            return CellDifference('{} != {}'.format(self.value, other.value))


class WorkbookDifference(dict):
    """ Difference between values of workbook """

    def __str__(self):
        """ Get string representation 

        Returns:
            :obj:`str`: string representation
        """
        diff = ''

        for name, sheet in self.items():
            diff += 'Sheet {}:\n  {}'.format(name, str(sheet).replace('\n', '\n  '))

        return diff


class WorksheetDifference(OrderedDict):
    """ Difference between values of worksheets """

    def __str__(self):
        """ Get string representation 

        Returns:
            :obj:`str`: string representation
        """
        diff = ''

        for i_row, row in self.items():
            diff += 'Row {}:\n  {}'.format(i_row + 1, str(row).replace('\n', '\n  '))

        return diff


class RowDifference(OrderedDict):
    """ Difference between values of rows """

    def __str__(self):
        """ Get string representation 

        Returns:
            :obj:`str`: string representation
        """
        diff = ''

        for i_col, cell_diff in self.items():
            diff += 'Cell {}: {}\n'.format(get_column_letter(i_col + 1), cell_diff)

        return diff[0:-1]


class CellDifference(str):
    """ Difference between values of cells """
    pass
