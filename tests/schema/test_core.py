""" Data model to represent models.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-11-23
:Copyright: 2016, Karr Lab
:License: MIT
"""

from enum import Enum
from wc_utils.schema import core
import re
import sys
import unittest


class Order(Enum):
    root = 1
    leaf = 2


class Root(core.Model):
    label = core.StringAttribute(verbose_name='Label', max_length=255, is_primary=True)

    class Meta(core.Model.Meta):
        pass


class Leaf(core.Model):
    root = core.ManyToOneAttribute(Root, verbose_name='Root',
                                   related_name='leaves', verbose_related_name='Leaves')
    id = core.RegexAttribute(verbose_name='ID', min_length=1, max_length=63,
                             pattern=r'^[a-z][a-z0-9_]*$', flags=re.I, is_primary=True)
    name = core.StringAttribute(verbose_name='Name', max_length=255)

    class Meta(core.Model.Meta):
        verbose_name = 'Leaf'
        verbose_name_plural = 'Leaves'
        attributes_order = ('id', )


class UnrootedLeaf(Leaf):
    name = core.StringAttribute(verbose_name='Name', max_length=10)

    root2 = core.ManyToOneAttribute(Root, is_none=True, verbose_name='Root', related_name='leaves2')
    id2 = core.RegexAttribute(verbose_name='ID', min_length=1, max_length=63,
                              pattern=r'^[a-z][a-z0-9_]*$', flags=re.I)
    name2 = core.StringAttribute(verbose_name='Name', min_length=2, max_length=3)
    float2 = core.FloatAttribute(verbose_name='Float', min=2., max=3.)
    float3 = core.FloatAttribute(verbose_name='Float', min=2.)
    enum2 = core.EnumAttribute(Order, verbose_name='Enum')
    enum3 = core.EnumAttribute(Order, verbose_name='Enum', default=Order['leaf'])
    multi_word_name = core.StringAttribute()


class Leaf3(UnrootedLeaf):

    class Meta(core.Model.Meta):
        attributes_order = ('id2', 'name2', )


class Grandparent(core.Model):
    id = core.StringAttribute(max_length=1, is_primary=True)


class Parent(core.Model):
    id = core.StringAttribute(max_length=2, is_primary=True)
    grandparent = core.ManyToOneAttribute(Grandparent, related_name='children')


class Child(core.Model):
    id = core.StringAttribute(is_primary=True)
    parent = core.ManyToOneAttribute(Parent, related_name='children')


class UniqueRoot(Root):
    label = core.SlugAttribute(verbose_name='Label', is_primary=True)

    class Meta(core.Model.Meta):
        pass


class TestCore(unittest.TestCase):

    def test_get_model(self):
        self.assertEqual(core.get_model('Root'), None)
        self.assertEqual(core.get_model(Root.__module__ + '.Root'), Root)

    def test_verbose_name(self):
        self.assertEqual(Root.Meta.verbose_name, 'Root')
        self.assertEqual(Root.Meta.verbose_name_plural, 'Roots')

        self.assertEqual(Leaf.Meta.verbose_name, 'Leaf')
        self.assertEqual(Leaf.Meta.verbose_name_plural, 'Leaves')

        self.assertEqual(UnrootedLeaf.Meta.verbose_name, 'Unrooted leaf')
        self.assertEqual(UnrootedLeaf.Meta.verbose_name_plural, 'Unrooted leaves')

        self.assertEqual(Leaf3.Meta.verbose_name, 'Leaf3')
        self.assertEqual(Leaf3.Meta.verbose_name_plural, 'Leaf3s')

        self.assertEqual(UnrootedLeaf.Meta.attributes['multi_word_name'].verbose_name, 'Multi word name')

    def test_meta_attributes(self):
        self.assertEqual(set(Root.Meta.attributes.keys()), set(('label', )))
        self.assertEqual(set(Leaf.Meta.attributes.keys()), set(('root', 'id', 'name', )))

    def test_meta_related_attributes(self):
        self.assertEqual(set(Root.Meta.related_attributes.keys()), set(('leaves', 'leaves2', )))
        self.assertEqual(set(Leaf.Meta.related_attributes.keys()), set())

    def test_attributes(self):
        root = Root()
        leaf = Leaf()
        self.assertEqual(set(vars(root).keys()), set(('label', '_leaves', '_leaves2', )))
        self.assertEqual(set(vars(leaf).keys()), set(('root', 'id', 'name')))

    def test_attributes_order(self):
        self.assertEqual(set(Root.Meta.attributes_order), set(Root.Meta.attributes.keys()))
        self.assertEqual(set(Leaf.Meta.attributes_order), set(Leaf.Meta.attributes.keys()))
        self.assertEqual(set(UnrootedLeaf.Meta.attributes_order), set(UnrootedLeaf.Meta.attributes.keys()))
        self.assertEqual(set(Leaf3.Meta.attributes_order), set(Leaf3.Meta.attributes.keys()))

        self.assertEqual(Root.Meta.attributes_order, ('label', ))
        self.assertEqual(Leaf.Meta.attributes_order, ('id', 'name', 'root'))
        self.assertEqual(UnrootedLeaf.Meta.attributes_order, (
            'id', 'name', 'root',
            'enum2', 'enum3', 'float2', 'float3', 'id2', 'multi_word_name', 'name2', 'root2', ))
        self.assertEqual(Leaf3.Meta.attributes_order, (
            'id2', 'name2',
            'enum2', 'enum3', 'float2', 'float3', 'id', 'multi_word_name', 'name', 'root', 'root2', ))

    def test_set(self):
        leaf = Leaf(id='leaf_1', name='Leaf 1')
        self.assertEqual(leaf.id, 'leaf_1')
        self.assertEqual(leaf.name, 'Leaf 1')

        leaf.id = 'leaf_2'
        leaf.name = 'Leaf 2'
        self.assertEqual(leaf.id, 'leaf_2')
        self.assertEqual(leaf.name, 'Leaf 2')

    def test_set_related(self):
        root1 = Root()
        root2 = Root()

        leaf1 = Leaf()
        leaf2 = Leaf()
        leaf3 = Leaf()
        self.assertEqual(leaf1.root, None)
        self.assertEqual(leaf2.root, None)
        self.assertEqual(leaf3.root, None)

        leaf1.root = root1
        leaf2.root = root1
        leaf3.root = root2
        self.assertEqual(leaf1.root, root1)
        self.assertEqual(leaf2.root, root1)
        self.assertEqual(leaf3.root, root2)
        self.assertEqual(root1.leaves, set((leaf1, leaf2)))
        self.assertEqual(root2.leaves, set((leaf3, )))

        leaf2.root = root2
        leaf3.root = root1
        self.assertEqual(leaf1.root, root1)
        self.assertEqual(leaf2.root, root2)
        self.assertEqual(leaf3.root, root1)
        self.assertEqual(root1.leaves, set((leaf1, leaf3, )))
        self.assertEqual(root2.leaves, set((leaf2, )))

        leaf4 = Leaf(root=root1)
        self.assertEqual(leaf4.root, root1)
        self.assertEqual(root1.leaves, set((leaf1, leaf3, leaf4)))

    def test_get_related(self):
        g0 = Grandparent(id='root-0')
        p0 = [
            Parent(grandparent=g0, id='node-0-0'),
            Parent(grandparent=g0, id='node-0-1'),
        ]
        c0 = [
            Child(parent=p0[0], id='leaf-0-0-0'),
            Child(parent=p0[0], id='leaf-0-0-1'),
            Child(parent=p0[1], id='leaf-0-1-0'),
            Child(parent=p0[1], id='leaf-0-1-1'),
        ]

        g1 = Grandparent(id='root-1')
        p1 = [
            Parent(grandparent=g1, id='node-1-0'),
            Parent(grandparent=g1, id='node-1-1'),
        ]
        c1 = [
            Child(parent=p1[0], id='leaf-1-0-0'),
            Child(parent=p1[0], id='leaf-1-0-1'),
            Child(parent=p1[1], id='leaf-1-1-0'),
            Child(parent=p1[1], id='leaf-1-1-1'),
        ]

        self.assertEqual(g0.get_related(), set((g0,)) | set(p0) | set(c0))
        self.assertEqual(p0[0].get_related(), set((g0,)) | set(p0) | set(c0))
        self.assertEqual(c0[0].get_related(), set((g0,)) | set(p0) | set(c0))

        self.assertEqual(g1.get_related(), set((g1,)) | set(p1) | set(c1))
        self.assertEqual(p1[0].get_related(), set((g1,)) | set(p1) | set(c1))
        self.assertEqual(c1[0].get_related(), set((g1,)) | set(p1) | set(c1))

    def test_equal(self):
        root1 = Root(label='a')
        root2 = Root(label='b')

        leaf1 = Leaf(root=root1, id='a', name='ab')
        leaf2 = Leaf(root=root1, id='a', name='ab')
        leaf3 = Leaf(root=root1, id='b', name='ab')
        leaf4 = Leaf(root=root2, id='b', name='ab')

        self.assertFalse(leaf1 is leaf2)
        self.assertFalse(leaf1 is leaf3)
        self.assertFalse(leaf2 is leaf3)

        self.assertTrue(leaf1 == leaf2)
        self.assertFalse(leaf1 == leaf3)
        self.assertTrue(leaf1 != leaf3)
        self.assertFalse(leaf1 != leaf2)

        self.assertEqual(leaf1, leaf2)
        self.assertNotEqual(leaf1, leaf3)

        self.assertNotEqual(leaf3, leaf4)
        self.assertTrue(leaf3 != leaf4)
        self.assertFalse(leaf3 == leaf4)

    def test_hash(self):
        self.assertEqual(len(set((Root(), ))), 1)
        self.assertEqual(len(set((Leaf(), Leaf(), ))), 2)
        self.assertEqual(len(set((UnrootedLeaf(), UnrootedLeaf()))), 2)
        self.assertEqual(len(set((Leaf3(), Leaf3(), Leaf3(), ))), 3)

    def test___str__(self):
        root = Root(label='test label')
        self.assertEqual(str(root), '<{}.{}: {}>'.format(Root.__module__, 'Root', root.label))

    def test_validate_attribute(self):
        root = Root()
        self.assertEqual(root.validate(), None)

        leaf = Leaf()
        self.assertEqual(set((x.attribute.name for x in leaf.validate().attributes)), set(('id', 'root',)))

        leaf.id = 'a'
        self.assertEqual(set((x.attribute.name for x in leaf.validate().attributes)), set(('root',)))

        leaf.name = 1
        self.assertEqual(set((x.attribute.name for x in leaf.validate().attributes)), set(('name', 'root',)))

        leaf.name = 'b'
        self.assertEqual(set((x.attribute.name for x in leaf.validate().attributes)), set(('root',)))

        leaf.root = root
        self.assertEqual(leaf.validate(), None)
        self.assertEqual(root.validate(), None)

        unrooted_leaf = UnrootedLeaf(root=root, id='a', id2='b', name2='ab', float2=2.4,
                                     float3=2.4, enum2=Order['root'], enum3=Order['leaf'])
        self.assertEqual(unrooted_leaf.validate(), None)

    def test_validate_string_attribute(self):
        leaf = UnrootedLeaf()

        leaf.name2 = 'a'
        self.assertIn('name2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.name2 = 'abcd'
        self.assertIn('name2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.name2 = 'ab'
        self.assertNotIn('name2', [x.attribute.name for x in leaf.validate().attributes])

    def test_validate_regex_attribute(self):
        leaf = Leaf()

        leaf.id = ''
        self.assertIn('id', [x.attribute.name for x in leaf.validate().attributes])

        leaf.id = '1'
        self.assertIn('id', [x.attribute.name for x in leaf.validate().attributes])

        leaf.id = 'a-'
        self.assertIn('id', [x.attribute.name for x in leaf.validate().attributes])

        leaf.id = 'a_'
        self.assertNotIn('id', [x.attribute.name for x in leaf.validate().attributes])

    def test_validate_slug_attribute(self):
        root = UniqueRoot(label='root-0')
        self.assertIn('label', [x.attribute.name for x in root.validate().attributes])

        root.label = 'root_0'
        self.assertEqual(root.validate(), None)

    def test_validate_float_attribute(self):
        leaf = UnrootedLeaf()

        # max=3.
        leaf.float2 = 'a'
        self.assertIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = 1
        self.assertIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = 4
        self.assertIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = 3
        self.assertNotIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = 3.
        self.assertNotIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = 2.
        self.assertNotIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = 2.5
        self.assertNotIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float2 = float('nan')
        self.assertIn('float2', [x.attribute.name for x in leaf.validate().attributes])

        # max=nan
        leaf.float3 = 2.5
        self.assertNotIn('float3', [x.attribute.name for x in leaf.validate().attributes])

        leaf.float3 = float('nan')
        self.assertIn('float3', [x.attribute.name for x in leaf.validate().attributes])

    def test_validate_enum_attribute(self):
        leaf = UnrootedLeaf()

        self.assertIn('enum2', [x.attribute.name for x in leaf.validate().attributes])
        self.assertNotIn('enum3', [x.attribute.name for x in leaf.validate().attributes])

        leaf.enum2 = Order['root']
        self.assertNotIn('enum2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.enum2 = 'root'
        self.assertNotIn('enum2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.enum2 = 1
        self.assertNotIn('enum2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.enum2 = 'root2'
        self.assertIn('enum2', [x.attribute.name for x in leaf.validate().attributes])

        leaf.enum2 = 3
        self.assertIn('enum2', [x.attribute.name for x in leaf.validate().attributes])

    def test_validate_manytoone_attribute(self):
        # is_none=False
        leaf = Leaf()
        self.assertIn('root', [x.attribute.name for x in leaf.validate().attributes])

        def set_root():
            leaf.root = Leaf()
        self.assertRaises(ValueError, set_root)

        leaf.root = Root()
        self.assertNotIn('root', [x.attribute.name for x in leaf.validate().attributes])

        # is_none=True
        unrooted_leaf = UnrootedLeaf()
        self.assertNotIn('root2', [x.attribute.name for x in unrooted_leaf.validate().attributes])

    def test_validate_objects(self):
        grandparent = Grandparent(id='root')
        parents = [
            Parent(grandparent=grandparent, id='node-0'),
            Parent(grandparent=grandparent),
        ]

        errors = core.validate_objects(parents)
        self.assertEqual(len(errors.objects), 1)
        self.assertEqual(errors.objects[0].object, parents[0])
        self.assertEqual(len(errors.objects[0].attributes), 1)
        self.assertEqual(errors.objects[0].attributes[0].attribute.name, 'id')

        roots = [
            Root(label='root-0'),
            Root(label='root-0'),
            Root(label='root-0'),
        ]
        errors = core.validate_objects(roots)
        self.assertEqual(errors, None)

        roots = [
            UniqueRoot(label='root_0'),
            UniqueRoot(label='root_0'),
            UniqueRoot(label='root_0'),
        ]
        errors = core.validate_objects(roots)
        self.assertEqual(len(errors.objects), 0)
        self.assertEqual(len(errors.models), 1)
        self.assertEqual(errors.models[0].model, UniqueRoot)
        self.assertEqual(len(errors.models[0].attributes), 1)
        self.assertEqual(errors.models[0].attributes[0].attribute.name, 'label')
        self.assertEqual(len(errors.models[0].attributes[0].messages), 1)
        self.assertRegexpMatches(errors.models[0].attributes[0].messages[0], '^Values must be unique\.')

    def test_inheritance(self):
        self.assertEqual(Leaf.Meta.attributes['name'].max_length, 255)
        self.assertEqual(UnrootedLeaf.Meta.attributes['name'].max_length, 10)

        self.assertEqual(set(Root.Meta.related_attributes.keys()), set(('leaves', 'leaves2')))

        self.assertEqual(Leaf.Meta.attributes['root'].primary_class, Leaf)
        self.assertEqual(Leaf.Meta.attributes['root'].related_class, Root)
        self.assertEqual(UnrootedLeaf.Meta.attributes['root'].primary_class, Leaf)
        self.assertEqual(UnrootedLeaf.Meta.attributes['root'].related_class, Root)
        self.assertEqual(Leaf3.Meta.attributes['root'].primary_class, Leaf)
        self.assertEqual(Leaf3.Meta.attributes['root'].related_class, Root)

        self.assertEqual(UnrootedLeaf.Meta.attributes['root2'].primary_class, UnrootedLeaf)
        self.assertEqual(UnrootedLeaf.Meta.attributes['root2'].related_class, Root)
        self.assertEqual(Leaf3.Meta.attributes['root2'].primary_class, UnrootedLeaf)
        self.assertEqual(Leaf3.Meta.attributes['root2'].related_class, Root)

        self.assertEqual(Root.Meta.related_attributes['leaves'].primary_class, Leaf)
        self.assertEqual(Root.Meta.related_attributes['leaves'].related_class, Root)

        self.assertEqual(Root.Meta.related_attributes['leaves2'].primary_class, UnrootedLeaf)
        self.assertEqual(Root.Meta.related_attributes['leaves2'].related_class, Root)

        root = Root()
        leaf = Leaf(root=root)
        unrooted_leaf = UnrootedLeaf(root=root)

        self.assertEqual(leaf.root, root)
        self.assertEqual(unrooted_leaf.root, root)
        self.assertEqual(root.leaves, set((leaf, unrooted_leaf, )))
