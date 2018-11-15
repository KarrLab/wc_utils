""" IO utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-28
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from abc import ABCMeta, abstractmethod
from datetime import datetime
from glob import glob
from itertools import chain
from math import isnan
from openpyxl import Workbook as XlsWorkbook, load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.styles.colors import Color
from openpyxl.utils import get_column_letter
from os.path import basename, dirname, splitext
from shutil import copyfile
from six import integer_types, string_types, with_metaclass
from wc_utils.workbook.core import Workbook, Worksheet, Row

import pyexcel


class Writer(with_metaclass(ABCMeta, object)):
    """ Write data to file(s)

    Attributes:
        path (:obj:`str`): path to file(s)
    """

    def __init__(self, path, title=None, description=None, keywords=None, version=None, language=None, creator=None):
        """
        Args:
            path (:obj:`str`): path to file(s)
            title (:obj:`str`, optional): title
            description (:obj:`str`, optional): description
            keywords (:obj:`str`, optional): keywords
            version (:obj:`str`, optional): version
            language (:obj:`str`, optional): language
            creator (:obj:`str`, optional): creator
        """
        self.path = path
        self.title = title
        self.description = description
        self.keywords = keywords
        self.version = version
        self.language = language
        self.creator = creator

    def run(self, data, style=None):
        """ Write workbook to file(s)

        Args:
            data (:obj:`Workbook`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
            style (:obj:`WorkbookStyle`, optional): workbook style
        """
        self.initialize_workbook()

        style = style or WorkbookStyle()
        for sheet_name, data_worksheet in data.items():
            style_worksheet = style.get(sheet_name, None)
            self.write_worksheet(sheet_name, data_worksheet, style=style_worksheet)

        self.finalize_workbook()

    @abstractmethod
    def initialize_workbook(self):
        """ Initialize workbook """
        pass  # pragma: no cover

    @abstractmethod
    def write_worksheet(self, sheet_name, data, style=None):
        """ Write worksheet to file

        Args:
            sheet_name (:obj:`str`): sheet name
            data (:obj:`Worksheet`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
            style (:obj:`WorksheetStyle`, optional): worksheet style
        """
        pass  # pragma: no cover

    @abstractmethod
    def finalize_workbook(self):
        """ Finalize workbook """
        pass  # pragma: no cover


class Reader(with_metaclass(ABCMeta, object)):
    """ Read data from file(s)

    Attributes:
        path (:obj:`str`): path to file(s)
    """

    def __init__(self, path):
        """
        Args:
            path (:obj:`str`): path to file(s)
        """
        self.path = path

    def run(self):
        """ Read data from file(s)

        Returns:
            :obj:`Workbook`: python representation of data
        """
        workbook = self.initialize_workbook()

        names = self.get_sheet_names()
        for name in names:
            workbook[name] = self.read_worksheet(name)

        return workbook

    @abstractmethod
    def initialize_workbook(self):
        """ Initialize workbook

        Returns:
            :obj:`Workbook`: data
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_sheet_names(self):
        """ Get names of sheets contained within path

        Returns:
            obj:`list` of `str`: list of sheet names
        """
        pass  # pragma: no cover

    @abstractmethod
    def read_worksheet(self, sheet_name, ignore_empty_final_rows=True, ignore_empty_final_cols=True):
        """ Read data from file

        Args:
            sheet_name (:obj:`str`): sheet name
            ignore_empty_final_rows (:obj:`bool`, optional): if :obj:`True`, ignore empty final rows
            ignore_empty_final_cols (:obj:`bool`, optional): if :obj:`True`, ignore empty final columns

        Returns:
            :obj:`Worksheet`: data
        """
        pass  # pragma: no cover


class ExcelWriter(Writer):
    """ Write data to Excel file

    Attributes:
        xls_workbook (:obj:`XlsWorkbook`): Excel workbook
    """

    def __init__(self, path, title=None, description=None, keywords=None, version=None, language=None,
                 creator=None):
        """
        Args:
            path (:obj:`str`): path to file(s)
            title (:obj:`str`, optional): title
            description (:obj:`str`, optional): description
            keywords (:obj:`str`, optional): keywords
            version (:obj:`str`, optional): version
            language (:obj:`str`, optional): language
            creator (:obj:`str`, optional): creator

        Raises:
            :obj:`ValueError`: if file extension is not '.xlsx'
        """
        _, ext = splitext(path)
        if ext != '.xlsx':
            raise ValueError("Extension of path '{}' must be '.xlsx'".format(path))

        super(ExcelWriter, self).__init__(path,
                                          title=title, description=description,
                                          keywords=keywords, version=version, language=language, creator=creator)
        self.xls_workbook = None

    def initialize_workbook(self):
        """ Initialize workbook """
        # Initialize workbook
        self.xls_workbook = xls_workbook = XlsWorkbook()
        xls_workbook.remove(xls_workbook.active)

        # set metadata
        props = xls_workbook.properties
        props.title = self.title
        props.description = self.description
        props.keywords = self.keywords
        props.version = self.version
        props.language = self.language
        props.creator = self.creator
        props.created = datetime.now()
        props.modified = props.created

    def write_worksheet(self, sheet_name, data, style=None):
        """ Write worksheet to file

        Args:
            sheet_name (:obj:`str`): sheet name
            data (:obj:`Worksheet`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
            style (:obj:`WorksheetStyle`, optional): worksheet style
        """
        xls_worksheet = self.xls_workbook.create_sheet(sheet_name)

        style = style or WorksheetStyle()
        alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

        if data:
            n_cols = max(len(row) for row in data)
        else:
            n_cols = 0
        frozen_rows = style.head_rows
        frozen_columns = style.head_columns
        row_height = style.row_height
        col_width = style.col_width
        head_font = Font(name=style.font_family, sz=style.font_size, bold=style.head_row_font_bold)
        body_font = Font(name=style.font_family, sz=style.font_size, bold=False)
        kwargs = {}
        if style.head_row_fill_pattern:
            kwargs['patternType'] = style.head_row_fill_pattern
        if style.head_row_fill_fgcolor:
            kwargs['fgColor'] = style.head_row_fill_fgcolor
        head_fill = PatternFill(**kwargs)

        if data:
            for i_col in range(1, n_cols + 1):
                col = xls_worksheet.column_dimensions[get_column_letter(i_col)]
                if not isnan(col_width):
                    col.width = col_width
                col.font = body_font

        for i_row, row in enumerate(data):
            xls_row = xls_worksheet.row_dimensions[i_row + 1]
            if i_row < frozen_rows or i_col < frozen_columns:
                xls_row.font = head_font
            else:
                xls_row.font = body_font

            for i_col, cell in enumerate(row):
                xls_cell = xls_worksheet.cell(row=i_row + 1, column=i_col + 1)

                value = cell
                if value is None:
                    pass
                elif isinstance(value, string_types):
                    data_type = Cell.TYPE_STRING
                elif isinstance(value, bool):
                    data_type = Cell.TYPE_BOOL
                elif isinstance(value, integer_types):
                    value = float(value)
                    data_type = Cell.TYPE_NUMERIC
                elif isinstance(value, float):
                    data_type = Cell.TYPE_NUMERIC
                else:
                    raise ValueError('Unsupported type {} at {}:{}:{}{}'.format(
                        value.__class__.__name__,
                        self.path, sheet_name, get_column_letter(i_col + 1), i_row + 1))

                if value is not None:
                    xls_cell.set_explicit_value(value=value, data_type=data_type)

                xls_cell.alignment = alignment

                if i_row < frozen_rows or i_col < frozen_columns:
                    if head_font:
                        xls_cell.font = head_font
                    if head_fill:
                        xls_cell.fill = head_fill
                else:
                    xls_cell.font = body_font

            if not isnan(row_height):
                xls_row.height = row_height
            xls_row.font = head_font

        xls_worksheet.freeze_panes = xls_worksheet.cell(row=frozen_rows + 1, column=frozen_columns + 1)

        if style.auto_filter and len(data) > 0 and len(data[0]) > 0 and frozen_rows > 0:
            xls_worksheet.auto_filter.ref = '{}{}:{}{}'.format(
                get_column_letter(1), frozen_rows,
                get_column_letter(n_cols), len(data))

    def finalize_workbook(self):
        """ Finalize workbook """
        self.xls_workbook.save(self.path)


class ExcelReader(Reader):
    """ Read data from Excel file

    Attributes:
        xls_workbook (:obj:`XlsWorkbook`): Excel workbook
    """

    def __init__(self, path):
        """
        Args:
            path (:obj:`str`): path to file(s)

        Raises:
            :obj:`ValueError`: if file extension is not '.xlsx'
        """
        _, ext = splitext(path)
        if ext != '.xlsx':
            raise ValueError("Extension of path '{}' must be '.xlsx'".format(path))
        super(ExcelReader, self).__init__(path)
        self.xls_workbook = None

    def initialize_workbook(self):
        """ Initialize workbook

        Returns:
            :obj:`Workbook`: data
        """
        self.xls_workbook = load_workbook(filename=self.path)
        return Workbook()

    def get_sheet_names(self):
        """ Get names of sheets contained within path

        Returns:
            obj:`list` of `str`: list of sheet names
        """
        return self.xls_workbook.sheetnames

    def read_worksheet(self, sheet_name, ignore_empty_final_rows=True, ignore_empty_final_cols=True):
        """ Read data from Excel worksheet

        Args:
            sheet_name (:obj:`str`): sheet name
            ignore_empty_final_rows (:obj:`bool`, optional): if :obj:`True`, ignore empty final rows
            ignore_empty_final_cols (:obj:`bool`, optional): if :obj:`True`, ignore empty final columns

        Returns:
            :obj:`Worksheet`: data

        Raises:
            :obj:`ValueError`: 
        """
        xls_worksheet = self.xls_workbook[sheet_name]
        worksheet = Worksheet()

        max_row = xls_worksheet.max_row
        max_col = xls_worksheet.max_column

        for i_row in range(1, max_row + 1):
            row = Row()
            worksheet.append(row)
            for i_col in range(1, max_col + 1):
                cell = xls_worksheet.cell(row=i_row, column=i_col)

                if cell.data_type in (Cell.TYPE_STRING, Cell.TYPE_INLINE, Cell.TYPE_NUMERIC, Cell.TYPE_NULL, Cell.TYPE_BOOL):
                    value = cell.value
                elif cell.data_type == Cell.TYPE_ERROR:
                    raise ValueError('Errors are not supported: {}:{}:{}{}'.format(self.path, sheet_name,
                                                                                   get_column_letter(i_col), i_row))
                elif cell.data_type in (Cell.TYPE_FORMULA, Cell.TYPE_FORMULA_CACHE_STRING):
                    if cell.value in ['=FALSE()', '=FALSE']:
                        value = False
                    elif cell.value in ['=TRUE()', '=TRUE']:
                        value = True
                    else:
                        raise ValueError('Formula are not supported: {}:{}:{}{}'.format(
                            self.path, sheet_name, get_column_letter(i_col), i_row))
                else:
                    raise ValueError('Unsupported data type: {} at {}:{}:{}{}'.format(
                        cell.data_type, self.path, sheet_name, get_column_letter(i_col), i_row))  # pragma: no cover # unreachable

                row.append(value)

        if ignore_empty_final_rows:
            worksheet.remove_empty_final_rows()

        if ignore_empty_final_cols:
            worksheet.remove_empty_final_cols()

        return worksheet


class SeparatedValuesWriter(Writer):
    """ Write data to csv/tsv file(s) """

    def __init__(self, path, title=None, description=None, keywords=None, version=None, language=None, creator=None):
        """
        Args:
            path (:obj:`str`): path to file(s)
            title (:obj:`str`, optional): title
            description (:obj:`str`, optional): description
            keywords (:obj:`str`, optional): keywords
            version (:obj:`str`, optional): version
            language (:obj:`str`, optional): language
            creator (:obj:`str`, optional): creator

        Raises:
            :obj:`ValueError`: if file extension is not '.csv' or '.tsv' or if file name pattern
                doesn't contain exactly one glob
        """
        _, ext = splitext(path)
        if ext not in ('.csv', '.tsv'):
            raise ValueError("Extension of path '{}' must be one of '.csv' or '.tsv'".format(
                path))

        if '*' in dirname(path):
            raise ValueError("path '{}' cannot have glob pattern '*' in its directory name".format(
                path))

        if basename(path).count('*') != 1:
            raise ValueError("path '{}' must have one glob pattern '*' in its base name".format(
                path))

        super(SeparatedValuesWriter, self).__init__(path,
                                                    title=title, description=description,
                                                    keywords=keywords, version=version, language=language, creator=creator)

    def initialize_workbook(self):
        """ Initialize workbook """
        pass

    def write_worksheet(self, sheet_name, data, style=None):
        """ Write worksheet to file

        Args:
            sheet_name (:obj:`str`): sheet name
            data (:obj:`Worksheet`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
            style (:obj:`WorksheetStyle`, optional): worksheet style
        """
        pyexcel.save_as(array=data, dest_file_name=self.path.replace('*', '{}').format(sheet_name))

    def finalize_workbook(self):
        """ Finalize workbook """
        pass


class SeparatedValuesReader(Reader):
    """ Read data from csv/tsv file(s) """

    def __init__(self, path):
        """
        Args:
            path (:obj:`str`): path to file(s)

        Raises:
            :obj:`ValueError`: if file extension is not '.csv' or '.tsv' or if file name pattern
                doesn't contain exactly one glob
        """
        _, ext = splitext(path)
        if ext not in ('.csv', '.tsv'):
            raise ValueError("Extension of path '{}' must be one of '.csv' or '.tsv'".format(
                path))

        if '*' in dirname(path):
            raise ValueError("path '{}' cannot have glob pattern '*' in its directory name".format(
                path))

        if basename(path).count('*') != 1:
            raise ValueError("path '{}' must have one glob pattern '*' in its base name".format(
                path))

        super(SeparatedValuesReader, self).__init__(path)

    def initialize_workbook(self):
        """ Initialize workbook

        Returns:
            :obj:`Workbook`: data
        """
        return Workbook()

    def get_sheet_names(self):
        """ Get names of sheets contained within path

        Returns:
            obj:`list` of `str`: list of sheet names

        Raises:
            :obj:`ValueError`: if glob does not find any matching files
        """
        i_glob = self.path.find('*')
        names = []
        for filename in glob(self.path):
            names.append(filename[i_glob:i_glob + len(filename) - len(self.path) + 1])
        if not names:
            raise ValueError("glob of path '{}' does not match any files".format(self.path))
        return names

    def read_worksheet(self, sheet_name, ignore_empty_final_rows=True, ignore_empty_final_cols=True):
        """ Read data from file

        Args:
            sheet_name (:obj:`str`): sheet name
            ignore_empty_final_rows (:obj:`bool`, optional): if :obj:`True`, ignore empty final rows
            ignore_empty_final_cols (:obj:`bool`, optional): if :obj:`True`, ignore empty final columns

        Returns:
            :obj:`Worksheet`: data
        """
        worksheet = Worksheet()
        # todo: skip_empty_rows=False is the default for pyexcel-io v >= 0.3.2
        # when it's available on pypi, set pyexcel>=0.4.0  pyexcel-io>=0.3.2 & remove skip_empty_rows option
        sv_worksheet = pyexcel.get_sheet(file_name=self.path.replace('*', '{}').format(sheet_name),
                                         skip_empty_rows=False)

        for sv_row in sv_worksheet.row:
            row = Row()
            worksheet.append(row)
            for sv_cell in sv_row:
                if sv_cell == '':
                    sv_cell = None
                elif sv_cell == 'True':
                    sv_cell = True
                elif sv_cell == 'False':
                    sv_cell = False

                row.append(sv_cell)

        if ignore_empty_final_rows:
            worksheet.remove_empty_final_rows()

        if ignore_empty_final_cols:
            worksheet.remove_empty_final_cols()

        return worksheet


def get_writer(extension):
    """ Get writer

    Args:
        extension (:obj:`str`): extension

    Returns:
        :obj:`class`: writer class

    Raises:
        :obj:`ValueError`: if extension is not one of ".xlsx", ".csv", or ".tsv"
    """
    if extension == '.xlsx':
        return ExcelWriter
    elif extension in ['.csv', '.tsv']:
        return SeparatedValuesWriter
    else:
        raise ValueError('Extension must be one of ".xlsx", ".csv", or ".tsv"')


def get_reader(extension):
    """ Get reader

    Args:
        extension (:obj:`str`): extension

    Returns:
        :obj:`class`: reader class

    Raises:
        :obj:`ValueError`: if extension is not one of ".xlsx", ".csv", or ".tsv"
    """
    if extension == '.xlsx':
        return ExcelReader
    elif extension in ['.csv', '.tsv']:
        return SeparatedValuesReader
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
    """
    # check extensions are valid
    _, ext = splitext(path)
    writer_cls = get_writer(ext)

    writer = writer_cls(path,
                        title=title, description=description, keywords=keywords,
                        version=version, language=language, creator=creator)
    writer.run(workbook, style=style)


def read(path):
    """ Read data from Excel (.xlsx) file or collection of comma separated (.csv) or tab separated (.tsv) file(s)

    Args:
        path (:obj:`str`): path to file(s)

    Returns:
        :obj:`Workbook`: python representation of data
    """
    # check extensions are valid
    _, ext = splitext(path)
    reader_cls = get_reader(ext)
    reader = reader_cls(path)
    return reader.run()


def convert(source, destination, worksheet_order=None, style=None, ignore_extra_sheets=True):
    """ Convert among Excel (.xlsx), comma separated (.csv), and tab separated formats (.tsv)

    Args:
        source (:obj:`str`): path to source file
        destination (:obj:`str`): path to save converted file
        worksheet_order (:obj:`list` of `str`): worksheet order
        style (:obj:`WorkbookStyle`, optional): workbook style for Excel
        ignore_extra_sheets (:obj:`bool`, optional): true/false should extra sheets in worksheet_order be ignored or should an error be thrown

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
    if ext_src == ext_dst and (worksheet_order is None or ext_src != '.xlsx'):
        if ext_src == '.xlsx':
            copyfile(source, destination)
        else:
            i_glob = source.find('*')
            dst_format = destination.replace('*', '{}')
            if not list(glob(source)):
                raise ValueError("glob of path '{}' does not match any files".format(source))
            for filename in glob(source):
                sheet_name = filename[i_glob:i_glob + len(filename) - len(source) + 1]
                copyfile(filename, dst_format.format(sheet_name))
        return

    # read, convert, and write
    workbook = read(source)

    ordered_workbook = Workbook()
    worksheet_order = worksheet_order or []
    if not ignore_extra_sheets:
        difference = set(worksheet_order) - set(workbook.keys())
        if difference:
            raise ValueError("source '{}' missing worksheets: '{}'".format(source, difference))

    for worksheet in chain(worksheet_order, workbook.keys()):
        if worksheet in workbook:
            ordered_workbook[worksheet] = workbook[worksheet]

    write(destination, ordered_workbook, style=style)


class WorkbookStyle(dict):
    """ Workbook style: dictionary of worksheet styles """
    pass


class WorksheetStyle(object):
    """ Worksheet style

    Attributes:
        head_rows (:obj:`int`): number of head rows
        head_columns (:obj:`int`): number of head columns
        head_row_font_bold (:obj:`bool`): head row bold
        head_row_fill_pattern (:obj:`str`): head row fill pattern
        head_row_fill_fgcolor (:obj:`str`): head row background color
        font_family (:obj:`str`): font family
        font_size (:obj:`float`): font size
        row_height (:obj:`float`): row height
        col_width (:obj:`float`): column width
        auto_filter (:obj:`bool`): whether or not to activate auto filters for row
    """

    def __init__(self, head_rows=0, head_columns=0, head_row_font_bold=False,
                 head_row_fill_pattern='solid', head_row_fill_fgcolor='',
                 font_family='Arial', font_size=11.,
                 row_height=15., col_width=15.,
                 auto_filter=True):
        """
        Args:
            head_rows (:obj:`int`, optional): number of head rows
            head_columns (:obj:`int`, optional): number of head columns
            head_row_font_bold (:obj:`bool`, optional): head row bold
            head_row_fill_pattern (:obj:`str`, optional): head row fill pattern
            head_row_fill_fgcolor (:obj:`str`, optional): head row background color
            font_family (:obj:`str`, optional): font family
            font_size (:obj:`float`, optional): font size
            row_height (:obj:`float`, optional): row height
            col_width (:obj:`float`, optional): column width
            auto_filter (:obj:`bool`, optional): whether or not to activate auto filters for row
        """
        self.head_rows = head_rows
        self.head_columns = head_columns
        self.head_row_font_bold = head_row_font_bold
        self.head_row_fill_pattern = head_row_fill_pattern
        self.head_row_fill_fgcolor = head_row_fill_fgcolor
        self.font_family = font_family
        self.font_size = font_size
        self.row_height = row_height
        self.col_width = col_width
        self.auto_filter = auto_filter
