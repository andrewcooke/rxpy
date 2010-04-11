

from unittest import TestCase

from rxpy.alphabet.base import CharSet


class CharSetTest(TestCase):
    
    def do_test_str(self, intervals, target):
        result = str(CharSet(intervals))
        assert result == target, result
    
    def test_str(self):
        self.do_test_str([], '[]')
        self.do_test_str([('a','a')], '[a]')
        self.do_test_str([('a','b')], '[ab]')
        self.do_test_str([('a','c')], '[a-c]')
        self.do_test_str([('a','a'), ('b', 'b')], '[ab]')
       
    def test_coallesce(self):
        self.do_test_str([('a','a'), ('c', 'c')], '[ac]')
        self.do_test_str([('a','a'), ('b', 'c')], '[a-c]')
        self.do_test_str([('a','b'), ('a', 'c')], '[a-c]')
        self.do_test_str([('a','b'), ('b', 'c')], '[a-c]')
        self.do_test_str([('a','c'), ('c', 'c')], '[a-c]')
        self.do_test_str([('b','c'), ('a', 'b')], '[a-c]')
        self.do_test_str([('c','c'), ('a', 'a')], '[ac]')
        self.do_test_str([('a','c'), ('p', 's')], '[a-cp-s]')
        self.do_test_str([('b','c'), ('p', 's')], '[bcp-s]')
        self.do_test_str([('b','c'), ('a', 's')], '[a-s]')
    
    def test_reversed(self):
        self.do_test_str([('c','a')], '[a-c]')
        self.do_test_str([('b','a')], '[ab]')
        self.do_test_str([('b','a'), ('b', 'c')], '[a-c]')
    
    def test_contains(self):
        assert 'a' not in CharSet([('b', 'b')])
        assert 'b' in CharSet([('b', 'b')])
        assert 'c' not in CharSet([('b', 'b')])
        assert 'a' in CharSet([('a', 'b')])
        assert 'b' in CharSet([('a', 'b')])
        assert 'c' not in CharSet([('a', 'b')])
        assert 'a' in CharSet([('a', 'c')])
        assert 'b' in CharSet([('a', 'c')])
        assert 'c' in CharSet([('a', 'c')])
        assert 'a' in CharSet([('a', 'b'), ('b', 'c')])
        assert 'b' in CharSet([('a', 'b'), ('b', 'c')])
        assert 'c' in CharSet([('a', 'b'), ('b', 'c')])
        assert 'a' in CharSet([('a', 'a'), ('c', 'c')])
        assert 'b' not in CharSet([('a', 'a'), ('c', 'c')])
        assert 'c' in CharSet([('a', 'a'), ('c', 'c')])
