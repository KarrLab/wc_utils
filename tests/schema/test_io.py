""" Test schema IO

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from wc_utils.schema import core, utils
from wc_utils.schema.io import Reader, Writer, convert, create_template
from wc_utils.workbook.io import WorksheetStyle, read as read_workbook
import os
import re
import shutil
import sys
import tempfile
import unittest


class Root(core.Model):
    id = core.StringAttribute(primary=True, unique=True)
    name = core.StringAttribute()

    class Meta(core.Model.Meta):
        attribute_order = ('id', 'name', )
        tabular_orientation = core.TabularOrientation.column


class Node(core.Model):
    id = core.SlugAttribute(primary=True)
    root = core.ManyToOneAttribute(Root, related_name='nodes')
    val1 = core.FloatAttribute()
    val2 = core.FloatAttribute()

    class Meta(core.Model.Meta):
        attribute_order = ('id', 'root', 'val1', 'val2', )


class OneToManyRowAttribute(core.OneToManyAttribute):
    pass


class OneToManyInlineAttribute(core.OneToManyAttribute):

    def serialize(self, value):
        return ', '.join([obj.id for obj in value])

    def deserialize(self, value, objects):
        if value:
            objs = []
            for id in value.split(', '):
                obj = OneToManyInline(id=id)
                if OneToManyInline not in objects:
                    objects[OneToManyInline] = {}
                objects[OneToManyInline][id] = obj
                objs.append(obj)

            return (objs, None)
        else:
            return (set(), None)


class Leaf(core.Model):
    id = core.StringAttribute(primary=True)
    nodes = core.ManyToManyAttribute(Node, related_name='leaves')
    val1 = core.FloatAttribute()
    val2 = core.FloatAttribute()
    onetomany_rows = OneToManyRowAttribute('OneToManyRow', related_name='leaf', related_none=False)
    onetomany_inlines = OneToManyInlineAttribute('OneToManyInline', related_name='leaf', related_none=False)

    class Meta(core.Model.Meta):
        attribute_order = (
            'id', 'nodes', 'val1', 'val2',
            'onetomany_rows', 'onetomany_inlines'
        )


class OneToManyRow(core.Model):
    id = core.SlugAttribute(primary=True)

    class Meta(core.Model.Meta):
        attribute_order = ('id',)


class OneToManyInline(core.Model):
    id = core.SlugAttribute(primary=False)

    class Meta(core.Model.Meta):
        attribute_order = ('id',)
        tabular_orientation = core.TabularOrientation.inline


class TestIo(unittest.TestCase):

    def setUp(self):
        self.root = root = Root(id='root', name=u'\u20ac')
        nodes = [
            Node(root=root, id='node_0', val1=1, val2=2),
            Node(root=root, id='node_1', val1=3, val2=4),
            Node(root=root, id='node_2', val1=5, val2=6),
        ]
        self.leaves = leaves = [
            Leaf(nodes=[nodes[0]], id='leaf_0_0', val1=7, val2=8),
            Leaf(nodes=[nodes[0]], id='leaf_0_1', val1=9, val2=10),
            Leaf(nodes=[nodes[1]], id='leaf_1_0', val1=11, val2=12),
            Leaf(nodes=[nodes[1]], id='leaf_1_1', val1=13, val2=14),
            Leaf(nodes=[nodes[2]], id='leaf_2_0', val1=15, val2=16),
            Leaf(nodes=[nodes[2]], id='leaf_2_1', val1=17, val2=18),
        ]
        leaves[0].onetomany_rows = [OneToManyRow(id='row_0_0'), OneToManyRow(id='row_0_1')]
        leaves[1].onetomany_rows = [OneToManyRow(id='row_1_0'), OneToManyRow(id='row_1_1')]
        leaves[2].onetomany_rows = [OneToManyRow(id='row_2_0'), OneToManyRow(id='row_2_1')]
        leaves[3].onetomany_rows = [OneToManyRow(id='row_3_0'), OneToManyRow(id='row_3_1')]
        leaves[4].onetomany_rows = [OneToManyRow(id='row_4_0'), OneToManyRow(id='row_4_1')]
        leaves[5].onetomany_rows = [OneToManyRow(id='row_5_0'), OneToManyRow(id='row_5_1')]

        leaves[0].onetomany_inlines = [OneToManyInline(id='inline_0_0'), OneToManyInline(id='inline_0_1')]
        leaves[1].onetomany_inlines = [OneToManyInline(id='inline_1_0'), OneToManyInline(id='inline_1_1')]
        leaves[2].onetomany_inlines = [OneToManyInline(id='inline_2_0'), OneToManyInline(id='inline_2_1')]
        leaves[3].onetomany_inlines = [OneToManyInline(id='inline_3_0'), OneToManyInline(id='inline_3_1')]
        leaves[4].onetomany_inlines = [OneToManyInline(id='inline_4_0'), OneToManyInline(id='inline_4_1')]
        leaves[5].onetomany_inlines = [OneToManyInline(id='inline_5_0'), OneToManyInline(id='inline_5_1')]

        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_write_read(self):
        # test integrity of relationships
        for leaf in self.leaves:
            for row in leaf.onetomany_rows:
                self.assertEqual(row.leaf, leaf)

        # write/read to/from Excel
        root = self.root
        objects = set((root, )) | root.get_related()
        objects = utils.group_objects_by_model(objects)

        filename = os.path.join(self.dirname, 'test.xlsx')
        Writer().run(filename, set((root,)), [Root, Node, Leaf, ])
        objects2 = Reader().run(filename, [Root, Node, Leaf, OneToManyRow])

        # validate
        all_objects2 = set()
        for model, model_objects in objects2.items():
            all_objects2.update(model_objects)
        self.assertEqual(core.Validator().run(all_objects2), None)

        # test objects saved and loaded correctly
        for model in objects.keys():
            self.assertEqual(len(objects2[model]), len(objects[model]),
                             msg='Different numbers of "{}" objects'.format(model.__name__))
        self.assertEqual(len(objects2), len(objects))

        root2 = objects2[Root].pop()

        filename2 = os.path.join(self.dirname, 'test2.xlsx')
        Writer().run(filename2, set((root2,)), [Root, Node, Leaf, ])
        original = read_workbook(filename)
        copy = read_workbook(filename2)
        self.assertEqual(copy, original)

        self.assertEqual(set([x.id for x in root2.nodes]), set([x.id for x in root.nodes]))
        self.assertEqual(root2, root)

        # unicode
        self.assertEqual(root2.name, u'\u20ac')

    def test_validation(self):
        t = Root(name='f')
        self.assertIn('value for primary attribute cannot be empty',
            t.validate().attributes[0].messages[0])

    def check_reader_errors(self, fixture_file, expected_messages, models, use_re=False,
        do_not_catch=False):
        ''' Run Reader expecting an error; check that the exception message matches expected messages

        Args:
            fixture_file (:obj:`str`): name of the file to be read
            expected_messages (:obj:`list` of `str`): list of expected strings or patterns in the
                exception
            models (:obj:`list` of `Model`): `Model`s for the schema of the data being read
            use_re (:obj:`boolean`, optional): if set, `expected_messages` contains RE patterns
            do_not_catch (:obj:`boolean`, optional): if set, run Reader() outside try ... catch;
                produces full exception message for debugging

        Raises:
            :obj:`Exception`: if do_not_catch
        '''
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', fixture_file)
        if do_not_catch:
            Reader().run(filename, models)
        with self.assertRaises(Exception) as context:
            Reader().run(filename, models)
        for msg in expected_messages:
            if not use_re:
                msg = re.escape(msg)
            self.assertRegexpMatches(str(context.exception), msg)

    def test_location_of_attrs(self):
        class Normal(core.Model):
            id = core.SlugAttribute()
            val = core.StringAttribute()

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'val')

        class Transposed(core.Model):
            tid = core.SlugAttribute()
            s = core.StringAttribute()

            class Meta(core.Model.Meta):
                attribute_order = ('tid', 's', )
                tabular_orientation = core.TabularOrientation.column

        file = 'test-locations.xlsx'
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', file)
        models = Reader().run(filename, [Normal, Transposed])
        ext = 'xlsx'
        normals = models[Normal]
        for obj in normals:
            if obj.val == 'x':
                (file_type, basename, worksheet, row, column) = obj.get_location('val')
                self.assertEqual(file_type, ext)
                self.assertEqual(basename, file)
                self.assertEqual(worksheet, obj.Meta.verbose_name_plural)
                self.assertEqual(row, 3)
                self.assertEqual(column, 'B')
                self.assertEqual(obj.location_report('val'),
                    ':'.join([file, obj.Meta.verbose_name_plural, "{}{}".format(column, row)]))

        transposeds = models[Transposed]
        for obj in transposeds:
            if obj.s == 'z':
                (file_type, basename, worksheet, row, column) = obj.get_location('s')
                self.assertEqual(file_type, ext)
                self.assertEqual(basename, file)
                self.assertEqual(worksheet, obj.Meta.verbose_name)
                self.assertEqual(row, 2)
                self.assertEqual(column, 'C')
                self.assertEqual(obj.location_report('s'),
                    ':'.join([file, obj.Meta.verbose_name, "{}{}".format(column, row)]))

        file = 'test-locations-*.csv'
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', file)
        models = Reader().run(filename, [Normal, Transposed])
        ext = 'csv'
        normals = models[Normal]
        for obj in normals:
            if obj.val == 'x':
                (file_type, basename, worksheet, row, column) = obj.get_location('val')
                self.assertEqual(file_type, ext)
                self.assertEqual(basename, file)
                self.assertEqual(row, 3)
                self.assertEqual(worksheet, obj.Meta.verbose_name_plural)
                self.assertEqual(column, 2)
                self.assertEqual(obj.location_report('val'),
                    ':'.join([file, obj.Meta.verbose_name_plural, "{},{}".format(row, column)]))

        transposeds = models[Transposed]
        for obj in transposeds:
            if obj.s == 'z':
                (file_type, basename, worksheet, row, column) = obj.get_location('s')
                self.assertEqual(file_type, ext)
                self.assertEqual(basename, file)
                self.assertEqual(worksheet, obj.Meta.verbose_name)
                self.assertEqual(row, 2)
                self.assertEqual(column, 3)
                self.assertEqual(obj.location_report('s'),
                    ':'.join([file, obj.Meta.verbose_name, "{},{}".format(row, column)]))

    def test_read_bad_headers(self):
        msgs = [
            "The model cannot be loaded because 'bad-headers.xlsx' contains error(s)",
            "Empty header field in row 1, col E - delete empty column(s)",
            "Header 'y' in row 1, col F does not match any attribute",
            "Roots\n",
            "Empty header field in row 3, col A - delete empty row(s)",]
        self.check_reader_errors('bad-headers.xlsx', msgs, [Root, Node, Leaf, OneToManyRow])

        msgs = [
            "The model cannot be loaded because 'bad-headers-*.csv' contains error(s)",
            "Header 'x' in row 5, col 1 does not match any attribute",
            "Nodes\n",
            "Empty header field in row 1, col 5 - delete empty column(s)",]
        self.check_reader_errors('bad-headers-*.csv', msgs, [Root, Node, Leaf, OneToManyRow])

        '''
        msgs = [
            "Duplicate, case insensitive, header fields: 'Root', 'root'",
            "Duplicate, case insensitive, header fields: 'good val', 'Good val', 'Good VAL'"]
        self.check_reader_errors('duplicate-headers.xlsx', msgs, [Node])
        '''

    def test_uncaught_data_error(self):
        class Test(core.Model):
            id = core.SlugAttribute(primary=True)
            float1 = core.FloatAttribute()
            bool1 = core.FloatAttribute()

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'float1', 'bool1', )

        msgs = ["The model cannot be loaded because 'uncaught-error.xlsx' contains error(s)",
            "uncaught-error.xlsx:Tests:B5",
            "float() argument must be a string or a number",
            "uncaught-error.xlsx:Tests:C6",
            "Value must be a `float`",]
        self.check_reader_errors('uncaught-error.xlsx', msgs, [Root, Test])

    def test_read_invalid_data(self):
        class NormalRecord(core.Model):
            id_with_underscores = core.SlugAttribute()
            val = core.StringAttribute(min_length=2)

            class Meta(core.Model.Meta):
                attribute_order = ('id_with_underscores', 'val')

        class Transposed(core.Model):
            id = core.SlugAttribute()
            val = core.StringAttribute(min_length=2)

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'val', )
                tabular_orientation = core.TabularOrientation.column

        RE_msgs = [
            "Leaves\n +'id':''\n +invalid-data.xlsx:Leaves:A6\n +StringAttribute value for primary "
                "attribute cannot be empty",
            "invalid-data.xlsx:'Normal records':B3",
            "Transposeds\n +'val':'x'\n +invalid-data.xlsx:Transposed:C2\n +Value must be at least "
                "2 characters",]
        self.check_reader_errors('invalid-data.xlsx', RE_msgs, [Leaf, NormalRecord, Transposed],
            use_re=True)

        RE_msgs = [
            "The model cannot be loaded because 'invalid-data-\*.csv' contains error",
            "Leaves *\n +'id':''\n +invalid-data-\*.csv:Leaves:6,1\n +StringAttribute value for "
                "primary attribute cannot be empty",
            "Transposeds\n +'val':'x'\n +invalid-data-\*.csv:Transposed:2,3\n +Value must be at "
                "least 2 characters",]
        self.check_reader_errors('invalid-data-*.csv', RE_msgs, [Leaf, NormalRecord, Transposed],
            use_re=True)

    def test_reference_errors(self):
        class NodeFriend(core.Model):
            id = core.SlugAttribute()
            node = core.OneToOneAttribute(Node, related_name='nodes')
            val = core.StringAttribute(min_length=2)

            class Meta(core.Model.Meta):
                attribute_order = ('id', 'val', 'node')

        RE_msgs = [
            "reference-errors.xlsx:Nodes:B3\n +Unable to find Root with id='not root'",
            "reference-errors.xlsx:Leaves:B6\n +Unable to find Node with id='no such node'",
            "reference-errors.xlsx:Leaves:E7\n +Unable to find OneToManyRow with id='no such row'",
            "reference-errors.xlsx:'Node friends':B2\n +Unable to find Node with id=no_node"]
        self.check_reader_errors('reference-errors.xlsx', RE_msgs, [Root, Node, Leaf, OneToManyRow,
            NodeFriend], use_re=True)

    def test_duplicate_primaries(self):
        RE_msgs = [
            "The model cannot be loaded because it fails to validate",
            "Node:\n +'id':\n +id values must be unique, but these values are repeated: node_2",
            "Root:\n +'id':\n +id values must be unique, but these values are repeated: 'root 2'"]
        self.check_reader_errors('duplicate-primaries.xlsx', RE_msgs, [Root, Node, Leaf, OneToManyRow],
            use_re=True)

    def test_create_worksheet_style(self):
        self.assertIsInstance(Writer.create_worksheet_style(Root), WorksheetStyle)

    def test_convert(self):
        filename_xls1 = os.path.join(self.dirname, 'test1.xlsx')
        filename_xls2 = os.path.join(self.dirname, 'test2_unreadable.xlsx')
        filename_csv = os.path.join(self.dirname, 'test-*.csv')

        models = [Root, Node, Leaf, ]
        Writer().run(filename_xls1, set((self.root,)), models)

        convert(filename_xls1, filename_csv, models)
        # this writes a workbook that Excel (Mac 2016) calls 'unreadable'
        # Excel also repairs the workbook and generates a "Repair result" xml file
        convert(filename_csv, filename_xls2, models)

    def test_create_template(self):
        filename = os.path.join(self.dirname, 'test3.xlsx')
        create_template(filename, [Root, Node, Leaf])
        objects = Reader().run(filename, [Root, Node, Leaf])
        self.assertEqual(objects, {
            Root: set(),
            Node: set(),
            Leaf: set(),
        })
        self.assertEqual(core.Validator().run([]), None)

    def run_options_tests(self, fixture_file):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', fixture_file)

        class SimpleModel(core.Model):
            val = core.StringAttribute(min_length=10)

        with self.assertRaises(ValueError) as context:
            # raises extra sheet exception
            Reader().run(filename, [SimpleModel])
        self.assertRegexpMatches(str(context.exception),
            "'test_run_options.*': No match .* model names {''} .* names {'extra sheet'}")

        with self.assertRaises(ValueError) as context:
            # raises extra attribute exception
            Reader().run(filename, [SimpleModel], ignore_other_sheets=True)
        self.assertRegexpMatches(str(context.exception),
            "The model cannot be loaded because 'test_run_options.*' contains error.*")
        if 'xlsx' in fixture_file:
            col = 'B'
        elif 'csv' in fixture_file:
            col = '2'
        self.assertRegexpMatches(str(context.exception),
            ".*Header 'extra' in row 1, col {} does not match any attribute.*".format(col))

        with self.assertRaises(ValueError) as context:
            # raises validation exception on 'too short'
            Reader().run(filename, [SimpleModel], ignore_other_sheets=True,
                skip_missing_attributes=True)
        self.assertRegexpMatches(str(context.exception),
            "The model cannot be loaded because 'test_run_options.*' contains error.*")
        if 'xlsx' in fixture_file:
            location = 'A3'
        elif 'csv' in fixture_file:
            location = '3,1'
        self.assertRegexpMatches(str(context.exception),
            ".*'val':'too short'\n.*test_run_options.*:'Simple models':{}\n.*"
                "Value must be at least 10 characters".format(location))

        class SimpleModel(core.Model):
            val = core.StringAttribute()
        model = Reader().run(filename, [SimpleModel], ignore_other_sheets=True,
            skip_missing_attributes=True)
        self.assertIn('too short', [r.val for r in model[SimpleModel]])

    def test_run_options(self):
        self.run_options_tests('test_run_options.xlsx')
        self.run_options_tests('test_run_options-*.csv')
