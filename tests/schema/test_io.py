""" Test schema IO

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""
from wc_utils.schema import core, utils
from wc_utils.schema.io import ExcelIo
import os
import sys
import tempfile
import unittest


class Root(core.Model):
    id = core.StringAttribute(primary=True, unique=True)
    name = core.StringAttribute()

    class Meta(core.Model.Meta):
        attribute_order = ('id', 'name', )
        tabular_orientation = core.TabularOrientation['column']


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
            return (set((OneToManyInline(x) for x in value.split(', '))), None)
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
        attribute_order = ('id', 'nodes', 'val1', 'val2', 'onetomany_rows', 'onetomany_inlines')


class OneToManyRow(core.Model):
    id = core.SlugAttribute(primary=True)

    class Meta(core.Model.Meta):
        attribute_order = ('id',)


class OneToManyInline(core.Model):
    id = core.SlugAttribute(primary=False)

    class Meta(core.Model.Meta):
        attribute_order = ('id',)
        tabular_orientation = core.TabularOrientation['inline']


class TestIo(unittest.TestCase):

    def setUp(self):
        _, self.filename = tempfile.mkstemp(suffix='.xlsx')

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    def test_write_read(self):
        root = Root(id='root', name='root')
        nodes = [
            Node(root=root, id=u'node-0-\u20ac', val1=1, val2=2),
            Node(root=root, id='node-1', val1=3, val2=4),
            Node(root=root, id='node-2', val1=5, val2=6),
        ]
        leaves = [
            Leaf(nodes=[nodes[0]], id='leaf-0-0', val1=7, val2=8),
            Leaf(nodes=[nodes[0]], id='leaf-0-1', val1=9, val2=10),
            Leaf(nodes=[nodes[1]], id='leaf-1-0', val1=11, val2=12),
            Leaf(nodes=[nodes[1]], id='leaf-1-1', val1=13, val2=14),
            Leaf(nodes=[nodes[2]], id='leaf-2-0', val1=15, val2=16),
            Leaf(nodes=[nodes[2]], id='leaf-2-1', val1=17, val2=18),
        ]
        leaves[0].onetomany_rows = [OneToManyRow(id='row_0_0'), OneToManyRow(id='row_0_1')]
        leaves[1].onetomany_rows = [OneToManyRow(id='row_1_0'), OneToManyRow(id='row_1_1')]
        leaves[2].onetomany_inlines = [OneToManyInline(id='inline_2_0'), OneToManyInline(id='inline_2_1')]
        leaves[3].onetomany_inlines = [OneToManyInline(id='inline_3_0'), OneToManyInline(id='inline_3_1')]

        objects = set((root, )) | root.get_related()
        objects = utils.group_objects_by_model(objects)

        root.clean()

        ExcelIo.write(self.filename, set((root,)), [Root, ])
        objects2 = ExcelIo.read(self.filename, set((Root, Node, Leaf, )))

        self.assertEqual(len(objects2[Root]), 1)

        root2 = objects2[Root].pop()
        self.assertEqual(root2, root)

        # unicode
        self.assertEqual(next(obj for obj in objects2[Node] if obj.val1 == 1).id, u'node-0-\u20ac')
