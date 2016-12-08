""" IO utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-28
:Copyright: 2016, Karr Lab
:License: MIT
"""

from datetime import datetime
from glob import glob
from math import isnan
from openpyxl import Workbook as XlsWorkbook, load_workbook
from openpyxl.cell.cell import Cell as CellType
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.styles.colors import Color
from os.path import basename, dirname, splitext
from shutil import copyfile
from six import integer_types, string_types
from wc_utils.workbook.core import Workbook, Worksheet, Row, Cell
import pyexcel


def read(path):
    """ Read data from Excel (.xlsx) file or collection of comma separated (.csv) or tab separated (.tsv) file(s)

    Args:
        path (:obj:`str`): path to file(s)

    Returns:
        :obj:`Workbook`: python representation of data

    Raises:
        :obj:`ValueError`: if extension is not one of ".xlsx", ".csv", or ".tsv"
    """
    # check extensions are valid
    _, ext = splitext(path)

    if ext == '.xlsx':
        return read_excel(path)
    elif ext in ['.csv', '.tsv']:
        return read_separated_values(path)
    else:
        raise ValueError('Extension must be one of ".xlsx", ".csv", or ".tsv"')


def write(path, workbook,
          title=None, description=None, keywords=None, version=None, language=None, creator=None,
          style=None):
    """ Write data to Excel (.xlsx) file or collection of comma separated (.csv) or tab separated (.tsv) file(s)

    Args:        
        path (:obj:`str`): path to file(s)
        workbook (:obj:`Workbook`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
        title (:obj:`str`, optional): title
        description (:obj:`str`, optional): description
        keywords (:obj:`str`, optional): keywords
        version (:obj:`str`, optional): version
        language (:obj:`str`, optional): language
        creator (:obj:`str`, optional): creator
        style (:obj:`WorkbookStyle`, optional): workbook style

    Raises:
        :obj:`ValueError`: if extension is not one of ".xlsx", ".csv", or ".tsv"
    """
    # check extensions are valid
    _, ext = splitext(path)

    if ext == '.xlsx':
        return write_excel(path, workbook, 
            title=title, description=description, keywords=keywords, 
            version=version, language=language, creator=creator,
            style=style)
    elif ext in ['.csv', '.tsv']:
        return write_separated_values(path, workbook)
    else:
        raise ValueError('Extension must be one of ".xlsx", ".csv", or ".tsv"')


def read_excel(filename):
    """ Read data from Excel workbook

    Args:
        filename (:obj:`str`): path to Excel file

    Returns:
        :obj:`Workbook`: python representation of data
    """
    workbook = Workbook()
    xls_workbook = load_workbook(filename=filename)
    for sheet_name in xls_workbook.get_sheet_names():
        xls_worksheet = xls_workbook[sheet_name]
        worksheet = workbook.worksheets[sheet_name] = Worksheet()

        for i_row in range(1, xls_worksheet.max_row + 1):
            row = Row()
            worksheet.rows.append(row)
            for i_col in range(1, xls_worksheet.max_column + 1):
                cell = Cell(xls_worksheet.cell(row=i_row, column=i_col).value)
                row.cells.append(cell)

    return workbook


def write_excel(filename, workbook,
                title=None, description=None, keywords=None, version=None, language=None, creator=None,
                style=None):
    """ Read data to an Excel workbook

    Args:        
        filename (:obj:`str`): path to Excel file
        workbook (:obj:`Workbook`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
        title (:obj:`str`, optional): title
        description (:obj:`str`, optional): description
        keywords (:obj:`str`, optional): keywords
        version (:obj:`str`, optional): version
        language (:obj:`str`, optional): language
        creator (:obj:`str`, optional): creator
        style (:obj:`WorkbookStyle`, optional): workbook style

    Raises:
        :obj:`ValueError`: if `workbook` contains values with are not strings, booleans, integers, floats, or None
    """

    style = style or WorkbookStyle()

    xls_workbook = XlsWorkbook()
    xls_workbook.remove_sheet(xls_workbook.active)

    props = xls_workbook.properties
    props.title = title
    props.description = description
    props.keywords = keywords
    props.version = version
    props.language = language
    props.creator = creator
    props.created = datetime.now()
    props.modified = props.created

    for sheet_name, worksheet in workbook.worksheets.items():
        xls_worksheet = xls_workbook.create_sheet(sheet_name)

        alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        if sheet_name in style.worksheets:
            sheet_style = style.worksheets[sheet_name]
        else:
            sheet_style = WorksheetStyle()

        frozen_rows = sheet_style.head_rows
        frozen_columns = sheet_style.head_columns
        row_height = sheet_style.row_height
        head_font = Font(bold=sheet_style.head_row_font_bold)
        kwargs = {}
        if sheet_style.head_row_fill_pattern:
            kwargs['patternType'] = sheet_style.head_row_fill_pattern
        if sheet_style.head_row_fill_fgcolor:
            kwargs['fgColor'] = sheet_style.head_row_fill_fgcolor
        head_fill = PatternFill(**kwargs)

        for i_row, row in enumerate(worksheet.rows):
            for i_col, cell in enumerate(row.cells):
                xls_cell = xls_worksheet.cell(row=i_row + 1, column=i_col + 1)

                value = cell.value
                if value is None:
                    pass
                elif isinstance(value, string_types):
                    data_type = CellType.TYPE_STRING
                elif isinstance(value, bool):
                    data_type = CellType.TYPE_BOOL
                elif isinstance(value, integer_types):
                    value = float(value)
                    data_type = CellType.TYPE_NUMERIC
                elif isinstance(value, float):
                    data_type = CellType.TYPE_NUMERIC
                else:
                    raise ValueError('Unsupported type {}'.format(value.__class__.__name__))

                if value is not None:
                    xls_cell.set_explicit_value(value=value, data_type=data_type)

                xls_cell.alignment = alignment

                if i_row < frozen_rows:
                    if head_font:
                        xls_cell.font = head_font
                    if head_fill:
                        xls_cell.fill = head_fill

            if not isnan(row_height):
                xls_worksheet.row_dimensions[i_row + 1].height = row_height

        xls_worksheet.freeze_panes = xls_worksheet.cell(row=frozen_rows + 1, column=frozen_columns + 1)

    xls_workbook.save(filename)


def read_separated_values(filename_pattern):
    """ Read data from a set of [tc]sv files

    Args:
        filename_pattern (:obj:`str`): pattern for file paths e.g. 'workbook-*.csv'

    Returns:
        :obj:`Workbook`: python representation of data

    Raises:
        :obj:`ValueError`: if file extension is not '.csv' or '.tsv' or if file name pattern doesn't contain exactly one glob
    """
    _, ext = splitext(filename_pattern)
    if ext not in ('.csv', '.tsv'):
        raise ValueError('Extension of `filename_pattern` must match be one of "csv" or "tsv"')

    if '*' in dirname(filename_pattern):
        raise ValueError('`filename_pattern` cannot have glob patterns in its dirrectory name')

    if basename(filename_pattern).count('*') != 1:
        raise ValueError('`filename_pattern` must have one glob pattern "*" in its base name')

    workbook = Workbook()
    i_glob = filename_pattern.find('*')
    for filename in glob(filename_pattern):
        sheet_name = filename[i_glob:i_glob + len(filename) - len(filename_pattern) + 1]
        worksheet = workbook.worksheets[sheet_name] = Worksheet()
        sv_worksheet = pyexcel.get_sheet(file_name=filename)

        for sv_row in sv_worksheet.row:
            row = Row()
            worksheet.rows.append(row)
            for sv_cell in sv_row:
                if sv_cell == '':
                    sv_cell = None
                elif sv_cell == 'True':
                    sv_cell = True
                elif sv_cell == 'False':
                    sv_cell = False

                row.cells.append(Cell(sv_cell))

    return workbook


def write_separated_values(filename_pattern, workbook):
    """ Write data to a set of [tc]sv files

    Args:        
        filename_pattern (:obj:`str`): template for file paths, e.g. 'workbook-*.csv'
        workbook (:obj:`Workbook`): python representation of data

    Raises:
        :obj:`ValueError`: if file extension is not '.csv' or '.tsv' or if file name pattern doesn't contain exactly one glob
    """
    _, ext = splitext(filename_pattern)
    if ext not in ('.csv', '.tsv'):
        raise ValueError('Extension of `filename_pattern` must match be one of "csv" or "tsv"')

    if '*' in dirname(filename_pattern):
        raise ValueError('`filename_pattern` cannot have glob patterns in its dirrectory name')

    if basename(filename_pattern).count('*') != 1:
        raise ValueError('`filename_pattern` must have one glob pattern "*" in its base name')

    for sheet_name, worksheet in workbook.worksheets.items():
        array = []
        for row in worksheet.rows:
            array.append([cell.value for cell in row.cells])

        pyexcel.save_as(array=array, dest_file_name=filename_pattern.replace('*', '{}').format(sheet_name))


def convert(source, destination, style=None):
    """ Convert among Excel (.xlsx), comma separated (.csv), and tab separated formats (.tsv) 

    Args:
        source (:obj:`str`): path to source file
        destination (:obj:`str`): path to save converted file
        style (:obj:`WorkbookStyle`, optional): workbook style for Excel

    Raises:
        :obj:`ValueError`: if file extensions are not supported or file names are equal
    """
    # check source != destination
    if source == destination:
        raise ValueError('Source and destination names must be different')

    # check extensions are valid
    _, ext_src = splitext(source)
    _, ext_dst = splitext(destination)

    if ext_src not in ['.xlsx', '.csv', '.tsv']:
        raise ValueError('Source extension must be one of ".xlsx", ".csv", or ".tsv"')

    if ext_dst not in ['.xlsx', '.csv', '.tsv']:
        raise ValueError('Destination extension must be one of ".xlsx", ".csv", or ".tsv"')

    # if extensions are the same, copy file(s)
    if ext_src == ext_dst:
        if ext_src == '.xlsx':
            copyfile(source, destination)
        else:
            i_glob = source.find('*')
            dst_format = destination.replace('*', '{}')
            for filename in glob(source):
                sheet_name = filename[i_glob:i_glob + len(filename) - len(source) + 1]
                copyfile(filename, dst_format.format(sheet_name))

    # read/write
    workbook = read(source)
    write(destination, workbook, style=style)


def convert_excel_to_separated_values(filename_excel, filename_pattern_separated_values):
    """ Convert an Excel workbook to a set of csv/tsv files

    Args:
        filename_pattern_separated_values (:obj:`str`): template for file paths, e.g. 'workbook-*.csv'
        filename_excel (:obj:`str`): path to Excel file
    """
    convert(filename_excel, filename_pattern_separated_values)


def convert_separated_values_to_excel(filename_pattern_separated_values, filename_excel, style=None):
    """ Convert a set of csv/tsv files to an Excel workbook

    Args:
        filename_pattern_separated_values (:obj:`str`): template for file paths, e.g. 'workbook-*.csv'
        filename_excel (:obj:`str`): path to Excel file
        style (:obj:`WorkbookStyle`, optional): workbook style
    """
    convert(filename_pattern_separated_values, filename_excel, style=style)


class WorkbookStyle(object):

    def __init__(self, worksheets=None):
        """
        Args:
            worksheets (:obj:`dict`, optional): dictionary of worksheet styles
        """
        self.worksheets = worksheets or {}


class WorksheetStyle(object):
    """ Represents an Excel worksheet

    Attributes:
        head_rows (:obj: `int`): number of head rows
        head_columns (:obj: `int`): number of head columns
        head_row_font_bold (:obj:`bool`): head row bold
        head_row_fill_pattern (:obj:`str`): head row fill pattern
        head_row_fill_fgcolor (:obj:`str`): head row background color
        row_height (:obj:`float`): row height
    """

    def __init__(self, head_rows=0, head_columns=0, head_row_font_bold=False, head_row_fill_pattern='solid', head_row_fill_fgcolor='', row_height=float('nan')):
        """
        Args:
            head_rows (:obj: `int`, optional): number of head rows
            head_columns (:obj: `int`, optional): number of head columns
            head_row_font_bold (:obj:`bool`, optional): head row bold
            head_row_fill_pattern (:obj:`str`, optional): head row fill pattern
            head_row_fill_fgcolor (:obj:`str`, optional): head row background color
            row_height (:obj:`float`, optional): row height
        """
        self.head_rows = head_rows
        self.head_columns = head_columns
        self.head_row_font_bold = head_row_font_bold
        self.head_row_fill_pattern = head_row_fill_pattern
        self.head_row_fill_fgcolor = head_row_fill_fgcolor
        self.row_height = row_height
