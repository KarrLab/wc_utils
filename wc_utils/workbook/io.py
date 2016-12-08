""" IO utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-28
:Copyright: 2016, Karr Lab
:License: MIT
"""

from abc import ABCMeta, abstractmethod
from datetime import datetime
from glob import glob
from math import isnan
from openpyxl import Workbook as XlsWorkbook, load_workbook
from openpyxl.cell.cell import Cell as CellType
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.styles.colors import Color
from os.path import basename, dirname, splitext
from shutil import copyfile
from six import integer_types, string_types, with_metaclass
from wc_utils.workbook.core import Workbook, Worksheet, Row, Cell
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
        for sheet_name, data_worksheet in data.worksheets.items():
            style_worksheet = style.worksheets.get(sheet_name, None)
            self.write_worksheet(sheet_name, data_worksheet, style=style_worksheet)

        self.finalize_workbook()

    @abstractmethod
    def initialize_workbook(self):
        """ Initialize workbook """
        pass

    @abstractmethod
    def write_worksheet(self, sheet_name, data, style=None):
        """ Write worksheet to file

        Args:
            sheet_name (:obj:`str`): sheet name
            data (:obj:`Worksheet`): python representation of data; each element must be a string, boolean, integer, float, or NoneType
            style (:obj:`WorksheetStyle`, optional): worksheet style
        """
        pass

    @abstractmethod
    def finalize_workbook(self):
        """ Finalize workbook """
        pass


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

        Args:
            path (:obj:`str`): path to file(s)

        Returns:
            :obj:`Workbook`: python representation of data
        """
        workbook = self.initialize_workbook()

        names = self.get_sheet_names()
        for name in names:
            workbook.worksheets[name] = self.read_worksheet(name)

        return workbook

    @abstractmethod
    def initialize_workbook(self):
        """ Initialize workbook 

        Returns:
            :obj:`Workbook`: data
        """
        pass

    @abstractmethod
    def get_sheet_names(self):
        """ Get names of sheets contained within path

        Returns:
            obj:`list` of `str`: list of sheet names
        """
        pass

    @abstractmethod
    def read_worksheet(self, sheet_name):
        """ Read data from file 

        Args:
            sheet_name (:obj:`str`): sheet name

        Returns:
            :obj:`Worksheet`: data
        """
        pass


class ExcelWriter(Writer):
    """ Write data to Excel file

    Attributes:
        xls_workbook (:obj:`XlsWorkbook`): Excel workbook
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

        Raises:
            :obj:`ValueError`: if file extension is not '.xlsx'
        """
        _, ext = splitext(path)
        if ext != '.xlsx':
            raise ValueError('Extension of `path` must one of ".xlsx"')

        super(ExcelWriter, self).__init__(path,
                                          title=title, description=description,
                                          keywords=keywords, version=version, language=language, creator=creator)
        self.xls_workbook = None

    def initialize_workbook(self):
        """ Initialize workbook """
        # Initialize workbook
        self.xls_workbook = xls_workbook = XlsWorkbook()
        xls_workbook.remove_sheet(xls_workbook.active)

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

        frozen_rows = style.head_rows
        frozen_columns = style.head_columns
        row_height = style.row_height
        head_font = Font(bold=style.head_row_font_bold)
        kwargs = {}
        if style.head_row_fill_pattern:
            kwargs['patternType'] = style.head_row_fill_pattern
        if style.head_row_fill_fgcolor:
            kwargs['fgColor'] = style.head_row_fill_fgcolor
        head_fill = PatternFill(**kwargs)

        for i_row, row in enumerate(data.rows):
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
            raise ValueError('Extension of `path` must one of ".xlsx"')
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

        Args:
            path (:obj:`str`): path to file(s)

        Returns:
            obj:`list` of `str`: list of sheet names
        """
        return self.xls_workbook.get_sheet_names()

    def read_worksheet(self, sheet_name):
        """ Read data from file 

        Args:
            sheet_name (:obj:`str`): sheet name

        Returns:
            :obj:`Worksheet`: data
        """
        xls_worksheet = self.xls_workbook[sheet_name]
        worksheet = Worksheet()

        for i_row in range(1, xls_worksheet.max_row + 1):
            row = Row()
            worksheet.rows.append(row)
            for i_col in range(1, xls_worksheet.max_column + 1):
                cell = Cell(xls_worksheet.cell(row=i_row, column=i_col).value)
                row.cells.append(cell)

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
            :obj:`ValueError`: if file extension is not '.csv' or '.tsv' or if file name pattern doesn't contain exactly one glob
        """
        _, ext = splitext(path)
        if ext not in ('.csv', '.tsv'):
            raise ValueError('Extension of `path` must match be one of ".csv" or ".tsv"')

        if '*' in dirname(path):
            raise ValueError('`path` cannot have glob patterns in its dirrectory name')

        if basename(path).count('*') != 1:
            raise ValueError('`path` must have one glob pattern "*" in its base name')

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
        array = []
        for row in data.rows:
            array.append([cell.value for cell in row.cells])

        pyexcel.save_as(array=array, dest_file_name=self.path.replace('*', '{}').format(sheet_name))

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
            :obj:`ValueError`: if file extension is not '.csv' or '.tsv' or if file name pattern doesn't contain exactly one glob
        """
        _, ext = splitext(path)
        if ext not in ('.csv', '.tsv'):
            raise ValueError('Extension of `path` must match be one of ".csv" or ".tsv"')

        if '*' in dirname(path):
            raise ValueError('`path` cannot have glob patterns in its dirrectory name')

        if basename(path).count('*') != 1:
            raise ValueError('`path` must have one glob pattern "*" in its base name')

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
        """
        i_glob = self.path.find('*')
        names = []
        for filename in glob(self.path):
            names.append(filename[i_glob:i_glob + len(filename) - len(self.path) + 1])
        return names

    def read_worksheet(self, sheet_name):
        """ Read data from file 

        Args:
            sheet_name (:obj:`str`): sheet name

        Returns:
            :obj:`Worksheet`: data
        """
        worksheet = Worksheet()
        sv_worksheet = pyexcel.get_sheet(file_name=self.path.replace('*', '{}').format(sheet_name))

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
