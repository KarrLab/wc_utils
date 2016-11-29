""" Data model to represent models.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""
from wc_utils.schema import core, utils
import sys
import unittest


class Root(core.Model):
    id = core.StringAttribute(max_length=1, primary=True, verbose_name='Identifier')


class Node(core.Model):
    id = core.StringAttribute(max_length=2, primary=True)
    root = core.ManyToOneAttribute(Root, related_name='nodes')


class Leaf(core.Model):
    id = core.StringAttribute(primary=True)
    node = core.ManyToOneAttribute(Node, related_name='leaves')


class TestUtils(unittest.TestCase):

    def test_get_attribute_by_verbose_name(self):
        self.assertEqual(utils.get_attribute_by_verbose_name(Root, 'Identifier'), Root.Meta.attributes['id'])
        self.assertEqual(utils.get_attribute_by_verbose_name(Root, 'Identifier2'), None)

    def test_group_objects_by_model(self):
        root = Root(id='root')
        nodes = [
            Node(root=root, id='node-0'),
            Node(root=root, id='node-1'),
        ]
        leaves = [
            Leaf(node=nodes[0], id='leaf-0-0'),
            Leaf(node=nodes[0], id='leaf-0-1'),
            Leaf(node=nodes[1], id='leaf-1-0'),
            Leaf(node=nodes[1], id='leaf-1-1'),
        ]
        objects = set((root,)) | set(nodes) | set(leaves)
        grouped_objects = utils.group_objects_by_model(objects)
        self.assertEqual(grouped_objects, {
            Root: set((root, )),
            Node: set(nodes),
            Leaf: set(leaves),
        })

    def test_get_related_errors(self):
        root = Root(id='root')
        nodes = [
            Node(root=root, id='node-0'),
            Node(root=root, id='node-1'),
        ]
        leaves = [
            Leaf(node=nodes[0], id='leaf-0-0'),
            Leaf(node=nodes[0], id='leaf-0-1'),
            Leaf(node=nodes[1], id='leaf-1-0'),
            Leaf(node=nodes[1], id='leaf-1-1'),
        ]

        errors = utils.get_related_errors(root)
        self.assertEqual(set((x.object for x in errors.objects)), set((root, )) | set(nodes))

        errors_by_model = utils.group_object_set_errors_by_model(errors)
        self.assertEqual(set((x.__name__ for x in errors_by_model.keys())), set(('Root', 'Node')))

        self.assertEqual(len(errors_by_model[Root]), 1)
        self.assertEqual(len(errors_by_model[Node]), 2)

        self.assertIsInstance(utils.get_object_set_error_string(errors), str)
