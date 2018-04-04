""" Caching tests

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-03-31
:Copyright: 2018, Karr Lab
:License: MIT
"""

import capturer
import os
import shutil
import tempfile
import unittest
import wc_utils.cache


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_memoize_positional_argument(self):
        cache = wc_utils.cache.Cache(directory=os.path.join(self.dir, 'cache'))

        call_count = 0

        @cache.memoize()
        def func(input):
            print('func ran')
            return 2 * input

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1), 2)
            self.assertEqual(captured.stdout.get_text(), '')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

    def test_memoize_keyword_argument(self):
        cache = wc_utils.cache.Cache(directory=os.path.join(self.dir, 'cache'))

        call_count = 0

        @cache.memoize()
        def func(input_1, input_2=1):
            print('func ran')
            return 2 * input_2

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1, input_2=1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1, input_2=1), 2)
            self.assertEqual(captured.stdout.get_text(), '')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1, input_2=2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(2, input_2=1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

    def test_memoize_filename_argument(self):
        cache = wc_utils.cache.Cache(directory=os.path.join(self.dir, 'cache'))

        call_count = 0

        @cache.memoize(filename_args=[0], filename_kwargs=['input_2'])
        def func(input_1, input_2=''):
            print('func ran')
            with open(input_2, 'r') as file:
                return 2 * float(file.read())

        fn_1 = os.path.join(self.dir, 'test_1')
        fn_2 = os.path.join(self.dir, 'test_2')
        fn_3 = os.path.join(self.dir, 'test_3')
        with open(fn_1, 'w') as file:
            file.write('1')
        with open(fn_2, 'w') as file:
            file.write('2')
        with open(fn_3, 'w') as file:
            file.write('3')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), '')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_3), 6)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_3, input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with open(fn_1, 'w') as file:
            file.write('1')
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with open(fn_1, 'w') as file:
            file.write('2')
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with open(fn_2, 'w') as file:
            file.write('2')
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with open(fn_2, 'w') as file:
            file.write('4')
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 8)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(fn_1, input_2=fn_2), 8)
            self.assertEqual(captured.stdout.get_text(), '')

    def test_memoize_filename_argument_glob(self):
        cache = wc_utils.cache.Cache(directory=os.path.join(self.dir, 'cache'))

        call_count = 0

        @cache.memoize(filename_args=[0], filename_kwargs=['input_2'])
        def func(input_1, input_2=''):
            print('func ran')
            with open(input_2, 'r') as file:
                return 2 * float(file.read())

        fn_1 = os.path.join(self.dir, 'test_1')
        fn_2 = os.path.join(self.dir, 'test_2')
        with open(fn_1, 'w') as file:
            file.write('1')
        with open(fn_2, 'w') as file:
            file.write('2')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(os.path.join(self.dir, 'test_*'), input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(os.path.join(self.dir, 'test_*'), input_2=fn_2), 4)
            self.assertEqual(captured.stdout.get_text(), '')

    def test_memoize_typed(self):
        cache = wc_utils.cache.Cache(directory=os.path.join(self.dir, 'cache'))

        call_count = 0

        @cache.memoize(typed=True)
        def func(input_1, input_2=None):
            print('func ran')
            return 2 * input_1

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1, input_2=1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1, input_2=1), 2)
            self.assertEqual(captured.stdout.get_text(), '')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1., input_2=1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1, input_2=1.), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1., input_2=1.), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func(1., input_2=1.), 2)
            self.assertEqual(captured.stdout.get_text(), '')

    def test_memoize_with_explicit_name(self):
        cache = wc_utils.cache.Cache(directory=os.path.join(self.dir, 'cache'))

        call_count = 0

        @cache.memoize(name='func_1_2')
        def func_1(input):
            print('func ran')
            return 2 * input

        @cache.memoize(name='func_1_2')
        def func_2(input):
            print('func ran')
            return 2 * input

        @cache.memoize(name='func_3')
        def func_3(input):
            print('func ran')
            return 2 * input

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func_1(1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func_2(1), 2)
            self.assertEqual(captured.stdout.get_text(), '')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            self.assertEqual(func_3(1), 2)
            self.assertEqual(captured.stdout.get_text(), 'func ran')

        with self.assertRaises(TypeError):
            cache.memoize(name=func_3)