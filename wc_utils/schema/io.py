""" Io

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from itertools import chain
from natsort import natsort_keygen, ns
from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from wc_utils.util.list import transpose
from wc_utils.schema import utils
from wc_utils.schema.core import Model, Attribute, RelatedAttribute, Validator, TabularOrientation
from six import string_types


class ExcelIo(object):

    @classmethod
    def write(cls, filename, objects, model_order):
        """ Write a set of model objects to an Excel workbook with one worksheet for each `Model`

        Args:
            filename (:obj:`str`): path to write Excel file
            objects (:obj:`set`): set of objects
            model_order (:obj:`list`): list of model, in the order that they should
                appear as worksheets; all models which are not in `model_order` will
                follow in alphabetical order
        """

        # get related objects
        more_objects = set()
        for obj in objects:
            more_objects.update(obj.get_related())

        # clean objects
        all_objects = objects | more_objects
        error = Validator().clean(all_objects)
        if error:
            raise(error)

        # group objects by class
        grouped_objects = {}
        for obj in all_objects:
            if obj.__class__ not in grouped_objects:
                grouped_objects[obj.__class__] = set()
            grouped_objects[obj.__class__].add(obj)

        # create workbook
        workbook = Workbook()

        # remove default sheet
        workbook.remove_sheet(workbook.active)

        # add sheets
        unordered_models = list(set(grouped_objects.keys()).difference(set(model_order)))
        unordered_models.sort(key=natsort_keygen(key=lambda model: model.Meta.verbose_name_plural, alg=ns.IGNORECASE))

        for model in chain(model_order, unordered_models):
            if model in grouped_objects:
                objects = grouped_objects[model]
            else:
                objects = set()
            cls.write_model(workbook, model, objects)

        # save workbook
        workbook.save(filename)

    @classmethod
    def write_model(cls, workbook, model, objects):
        """ Write a set of model objects to an Excel worksheet

        Args:
            workbook (:obj:`Workbook`): workbook
            model (:obj:`class`): model
            objects (:obj:`set` of `Model`): set of instances of `model`
        """

        # attribute order
        attributes = [model.Meta.attributes[attr_name] for attr_name in model.Meta.attribute_order]

        # column labels
        headings = [[attr.verbose_name for attr in attributes]]

        # objects
        objects = list(objects)
        objects.sort(key=natsort_keygen(key=lambda obj: obj.get_primary_attribute(), alg=ns.IGNORECASE))

        data = []
        for obj in objects:
            obj_data = []
            for attr in attributes:
                obj_data.append(attr.serialize(getattr(obj, attr.name)))
            data.append(obj_data)

        # transpose data for column orientation
        if model.Meta.tabular_orientation == TabularOrientation['row']:
            cls.write_sheet(workbook,
                            sheet_name=model.Meta.verbose_name_plural,
                            data=data,
                            column_headings=headings,
                            frozen_rows=1,
                            frozen_columns=model.Meta.frozen_columns,
                            )
        else:
            cls.write_sheet(workbook,
                            sheet_name=model.Meta.verbose_name_plural,
                            data=transpose(data),
                            row_headings=headings,
                            frozen_rows=model.Meta.frozen_columns,
                            frozen_columns=1,
                            )

    @staticmethod
    def write_sheet(workbook, sheet_name, data,
                    row_headings=None, column_headings=None,
                    frozen_rows=0, frozen_columns=0):
        """ Write data to sheet

        Args:
            workbook (:obj:`Workbook`): workbook
            sheet_name (:obj:`str`): sheet name
            data (:obj:`list` of `list` of `object`): list of list of cell values
            row_headings (:obj:`list` of `list` of `str`, optional): list of list of row headings
            column_headings (:obj:`list` of `list` of `str`, optional): list of list of column headings
            frozen_rows (:obj:`int`, optional): number of rows to freeze
            frozen_columns (:obj:`int`, optional): number of columns to freeze
        """
        row_headings = row_headings or []
        column_headings = column_headings or []

        # create sheet
        ws = workbook.create_sheet(sheet_name)

        # initialize styling
        ws.freeze_panes = ws.cell(row=frozen_rows + 1, column=frozen_columns + 1)

        alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        fill = PatternFill("solid", fgColor='CCCCCC')
        font = Font(bold=True)
        height = 15

        # row headings
        for i_col, row_headings_col in enumerate(row_headings):
            for i_row, heading in enumerate(row_headings_col):
                cell = ws.cell(row=1 + len(column_headings) + i_row, column=1 + i_col)
                cell.value = heading
                cell.alignment = alignment
                cell.fill = fill
                cell.font = font

        # column headings
        for i_row, column_headings_row in enumerate(column_headings):
            for i_col, heading in enumerate(column_headings_row):
                cell = ws.cell(row=1 + i_row, column=1 + len(row_headings) + i_col)
                cell.value = heading
                cell.alignment = alignment
                cell.fill = fill
                cell.font = font

        # data
        for i_row, data_row in enumerate(data):
            for i_col, value in enumerate(data_row):
                cell = ws.cell(row=1 + len(column_headings) + i_row, column=1 + len(row_headings) + i_col)

                if isinstance(value, string_types):
                    data_type = Cell.TYPE_STRING
                elif isinstance(value, bool):
                    data_type = Cell.TYPE_BOOL
                elif isinstance(value, float):
                    data_type = Cell.TYPE_NUMERIC
                else:
                    raise ValueError('Cannot save values of type "{}"'.format(value.__class__.__name__))

                if value is not None:
                    cell.set_explicit_value(value=value, data_type=data_type)
                cell.alignment = alignment

        # row heights
        for i_row in range(1, ws.max_row + 1):
            ws.row_dimensions[i_row].height = height

    @classmethod
    def read(cls, filename, models):
        """ Read a set of model objects from an Excel workbook

        Args:
            filename (:obj:`str`): path to Excel worksheet
            models (:obj:`set` of `class`): set of models

        Returns:
            :obj:`dict`: model objects grouped by `Model`
        """
        # load workbook
        workbook = load_workbook(filename=filename)

        # read objects
        errors = {}
        objects = {}
        for model in models:
            model_objects, model_errors = cls.read_model(workbook, model, objects, set_related=False)
            if model_objects:
                objects[model] = model_objects
            if model_errors:
                errors[model] = model_errors

        if errors:
            msg = 'The model cannot be loaded because the spreadsheet contains error(s):\n'
            for model, model_errors in errors.items():
                msg += '- {}:\n  - {}\n'.format(model.__name__, '\n  - '.join(model_errors))
            ValueError(msg)

        # link objects
        errors = {}
        for model in models:
            _, model_errors = cls.read_model(workbook, model, objects, set_related=True)
            if model_errors:
                errors[model] = model_errors

        if errors:
            msg = 'The model cannot be loaded because the spreadsheet contains error(s):\n'
            for model, model_errors in errors.items():
                msg += '- {}:\n  - {}\n'.format(model.__name__, '\n  - '.join(model_errors))
            ValueError(msg)

        # convert to sets
        for model in models:
            objects[model] = set(objects[model])

        # validate
        all_objects = set()
        for model in models:
            all_objects.update(objects[model])

        errors = Validator().run(all_objects)
        if errors:
            ValueError(utils.get_object_set_error_string(errors))

        # return
        return objects

    @classmethod
    def read_model(cls, workbook, model, all_objects, set_related=False):
        """ Read a set of objects from an Excel worksheet

        Args:
            workbook (:obj:`Workbook`): workbook
            model (:obj:`class`): model
            all_objects (:obj:`dict`): dictionary of model object grouped by model
            set_related (:obj:`bool`, optional): if true, set values of `RelatedAttribute`

        Returns:
            :obj:`tuple` of `list` of `Model`, `list` of `str`: tuple of a list of objects and 
                a list of parsing errors
        """
        if model.Meta.verbose_name_plural not in workbook:
            return ([], None)

        # get worksheet
        if model.Meta.tabular_orientation == TabularOrientation['row']:
            data, _, headings = cls.read_sheet(
                workbook,
                model.Meta.verbose_name_plural,
                num_column_heading_rows=1)
        else:
            data, headings, _ = cls.read_sheet(
                workbook,
                model.Meta.verbose_name_plural,
                num_row_heading_columns=1)
            data = transpose(data)
        headings = headings[0]

        # get attributes order
        attributes = [model.Meta.attributes[attr_name] for attr_name in model.Meta.attribute_order]

        # sort attributes by header order
        attributes = []
        errors = []
        for verbose_name in headings:
            attr = utils.get_attribute_by_verbose_name(model, verbose_name)
            if attr is None:
                errors.append('Header "{}" does not match any attributes'.format(verbose_name))
            else:
                attributes.append(attr)

        if errors:
            return (None, errors)

        # read data
        objects = list()
        errors = []
        for obj_data in data:
            obj = model()

            for attr, attr_value in zip(attributes, obj_data):
                if not set_related and not isinstance(attr, RelatedAttribute):
                    value, error = attr.deserialize(attr_value)
                    if error:
                        errors.append(error)
                    else:
                        setattr(obj, attr.name, value)

                elif set_related and isinstance(attr, RelatedAttribute):
                    value, error = attr.deserialize(attr_value, all_objects)
                    if error:
                        errors.append(error)
                    else:
                        setattr(obj, attr.name, value)

            objects.append(obj)

        return (objects, errors)

    @staticmethod
    def read_sheet(workbook, sheet_name, num_row_heading_columns=0, num_column_heading_rows=0):
        """ Read an Excel sheet in to a two-dimensioanl list

        Args:
            workbook (:obj:`Workbook`): workbook
            sheet_name (:obj:`str`): worksheet name
            num_row_heading_columns (:obj:`int`, optional): number of columns of row headings
            num_column_heading_rows (:obj:`int`, optional): number of rows of column headings

        Returns:
            :obj:`list` of `list`: two-dimensional list of table values
        """
        ws = workbook[sheet_name]

        row_headings = []
        for i_col in range(1, num_row_heading_columns + 1):
            row_headings_col = []
            row_headings.append(row_headings_col)
            for i_row in range(1 + num_column_heading_rows, ws.max_row + 1):
                row_headings_col.append(ws.cell(row=i_row, column=i_col).value)

        column_headings = []
        for i_row in range(1, num_column_heading_rows + 1):
            column_headings_row = []
            column_headings.append(column_headings_row)
            for i_col in range(1 + num_row_heading_columns, ws.max_column + 1):
                column_headings_row.append(ws.cell(row=i_row, column=i_col).value)

        data = []
        for i_row in range(1 + num_column_heading_rows, ws.max_row + 1):
            data_row = []
            data.append(data_row)
            for i_col in range(1 + num_row_heading_columns, ws.max_column + 1):
                data_row.append(ws.cell(row=i_row, column=i_col).value)

        return (data, row_headings, column_headings)
