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
    id = core.StringAttribute(primary=True)
    name = core.StringAttribute()

    class Meta(core.Model.Meta):
        attributes_order = ('id', 'name', )


class Node(core.Model):
    id = core.StringAttribute(primary=True)
    root = core.ManyToOneAttribute(Root, related_name='nodes')
    val1 = core.FloatAttribute()
    val2 = core.FloatAttribute()

    class Meta(core.Model.Meta):
        attributes_order = ('id', 'root', 'val1', 'val2', )


class Leaf(core.Model):
    id = core.StringAttribute(primary=True)
    node = core.ManyToOneAttribute(Node, related_name='leaves')
    val1 = core.FloatAttribute()
    val2 = core.FloatAttribute()

    class Meta(core.Model.Meta):
        attributes_order = ('id', 'node', 'val1', 'val2', )


class TestIo(unittest.TestCase):

    def setUp(self):
        _, self.filename = tempfile.mkstemp(suffix='.xlsx')

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    def test_write_read(self):
        root = Root(id='root', name='root')
        nodes = [
            Node(root=root, id='node-0', val1=1, val2=2),
            Node(root=root, id='node-1', val1=3, val2=4),
            Node(root=root, id='node-2', val1=5, val2=6),
        ]
        leaves = [
            Leaf(node=nodes[0], id='leaf-0-0', val1=7, val2=8),
            Leaf(node=nodes[0], id='leaf-0-1', val1=9, val2=10),
            Leaf(node=nodes[1], id='leaf-1-0', val1=11, val2=12),
            Leaf(node=nodes[1], id='leaf-1-1', val1=13, val2=14),
            Leaf(node=nodes[2], id='leaf-2-0', val1=15, val2=16),
            Leaf(node=nodes[2], id='leaf-2-1', val1=17, val2=18),
        ]

        objects = set((root, )) | root.get_related()
        objects = utils.group_objects_by_model(objects)

        root.clean()

        ExcelIo.write(self.filename, set((root,)), [Root, ])
        objects2 = ExcelIo.read(self.filename, set((Root, Node, Leaf, )))

        self.assertEqual(len(objects2[Root]), 1)

        root2 = objects2[Root].pop()
        self.assertEqual(root2, root)
