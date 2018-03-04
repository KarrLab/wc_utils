"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-03-03
:Copyright: 2018, Karr Lab
:License: MIT
"""
import random
import unittest
from wc_utils.util import heapq


# test only the heapq function wc_sim uses: _siftup()
class TestHeapq(unittest.TestCase):

    def setUp(self):
        self.heap_len = 50
        # to make the data easier to see self.heap entries have different values than self.heap positions
        self.heap = [i+self.heap_len for i in range(self.heap_len)]

    def test__siftup_n_siftdown(self):
        num_tests = 1000
        for j in range(num_tests):
            pos = random.choice(range(self.heap_len))
            val = random.choice(range(self.heap_len))+self.heap_len
            self.heap[pos] = val
            heapq._siftup(self.heap, pos)
            self.assertTrue(heapq.heap_test(self.heap))
