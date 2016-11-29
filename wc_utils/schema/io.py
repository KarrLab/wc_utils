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
from wc_utils.schema import utils
from wc_utils.schema.core import Model, Attribute, RelatedAttribute, clean_objects, clean_and_validate_objects


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
        error = clean_objects(all_objects)
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

        # create new worksheet
        ws = workbook.create_sheet(model.Meta.verbose_name_plural)

        # styling
        ws.freeze_panes = ws.cell(column=model.Meta.num_frozen_columns + 1, row=2)

        alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        fill = PatternFill("solid", fgColor='CCCCCC')
        font = Font(bold=True)
        height = 15

        # attribute order
        attributes = [model.Meta.attributes[attr_name] for attr_name in model.Meta.attributes_order]

        # column labels
        for i_attr, attr in enumerate(attributes):
            cell = ws.cell(row=1, column=1 + i_attr)
            cell.value = attr.verbose_name
            cell.alignment = alignment
            cell.fill = fill
            cell.font = font

        ws.row_dimensions[1].height = height

        # objects
        objects = list(objects)
        objects.sort(key=natsort_keygen(key=lambda obj: obj.get_primary_attribute(), alg=ns.IGNORECASE))

        for i_obj, obj in enumerate(objects):
            for i_attr, attr in enumerate(attributes):
                cell = ws.cell(row=2 + i_obj, column=1 + i_attr)

                value = attr.serialize(getattr(obj, attr.name))
                if isinstance(value, str):
                    data_type = Cell.TYPE_STRING
                elif isinstance(value, bool):
                    data_type = Cell.TYPE_BOOL
                elif isinstance(value, float):
                    data_type = Cell.TYPE_NUMERIC
                else:
                    raise ValueError('Cannot save values of type "{}" for {}.{}'.format(
                        value.__class__.__name__, obj.__class__.__name__, attr.name))

                if value is not None:
                    cell.set_explicit_value(value=value, data_type=data_type)
                cell.alignment = alignment

            ws.row_dimensions[2 + i_obj].height = height

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

        errors = clean_and_validate_objects(all_objects)
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
            :obj:`set` of `Model`: set of objects
        """
        if model.Meta.verbose_name_plural not in workbook:
            return set()

        # get workshet
        ws = workbook[model.Meta.verbose_name_plural]

        # get attributes order
        attributes = [model.Meta.attributes[attr_name] for attr_name in model.Meta.attributes_order]

        # read headers
        attributes = []
        errors = []
        for i_col in range(1, ws.max_column + 1):
            verbose_name = ws.cell(row=1, column=i_col).value
            attr = utils.get_attribute_by_verbose_name(model, verbose_name)
            if attr is None:
                errors.append('Header "{}" at {}1 does not match any attributes'.format(
                    verbose_name, get_column_letter(i_col)))
            else:
                attributes.append(attr)

        if errors:
            return (None, errors)

        # read data
        objects = list()
        errors = []
        for i_row in range(2, ws.max_row + 1):
            obj = model()

            for i_attr, attr in enumerate(attributes):
                cell = ws.cell(row=i_row, column=i_attr + 1)

                if not set_related and not isinstance(attr, RelatedAttribute):
                    value, error = attr.deserialize(cell.value)
                    if error:
                        errors.append(error)
                    else:
                        setattr(obj, attr.name, value)

                elif set_related and isinstance(attr, RelatedAttribute):
                    value, error = attr.deserialize(cell.value, all_objects)
                    if error:
                        errors.append(error)
                    else:
                        setattr(obj, attr.name, value)

            objects.append(obj)

        return (objects, errors)
