
from unittest import TestCase

from rxpy.alphabet.unicode import Unicode
from rxpy.direct.visitor import Visitor
from rxpy.parser._test.parser import parse


class VisitorTest(TestCase):
    
    def test_string(self):
        assert Visitor(Unicode(), parse('abc'), 'abc')
        assert Visitor(Unicode(), parse('abc'), 'abcd')
        assert not Visitor(Unicode(), parse('abc'), 'ab')
        
    def test_dot(self):
        assert Visitor(Unicode(), parse('a.c'), 'abc')
        assert Visitor(Unicode(), parse('...'), 'abcd')
        assert not Visitor(Unicode(), parse('...'), 'ab')
        
    def test_char(self):
        assert Visitor(Unicode(), parse('[ab]'), 'a')
        assert Visitor(Unicode(), parse('[ab]'), 'b')
        assert not Visitor(Unicode(), parse('[ab]'), 'c')

    def test_group(self):
        v = Visitor(Unicode(), parse('(.).'), 'ab')
        assert len(v.groups) == 1, len(v.groups)
        v = Visitor(Unicode(), parse('((.).)'), 'ab')
        assert len(v.groups) == 2, len(v.groups)
        
    def test_group_reference(self):
        assert Visitor(Unicode(), parse('(.)\\1'), 'aa')
        assert not Visitor(Unicode(), parse('(.)\\1'), 'ab')
 
    def test_split(self):
        assert Visitor(Unicode(), parse('a*b'), 'b')
        assert Visitor(Unicode(), parse('a*b'), 'ab')
        assert Visitor(Unicode(), parse('a*b'), 'aab')
        assert not Visitor(Unicode(), parse('a*b'), 'aa')
        
    def test_nested_group(self):
        v = Visitor(Unicode(), parse('(.)*'), 'ab')
        assert len(v.groups) == 1

    def test_lookahead(self):
        assert Visitor(Unicode(), parse('a(?=b)'), 'ab')
        assert not Visitor(Unicode(), parse('a(?=b)'), 'ac')
        assert not Visitor(Unicode(), parse('a(?!b)'), 'ab')
        assert Visitor(Unicode(), parse('a(?!b)'), 'ac')
    
    def test_lookback(self):
        assert Visitor(Unicode(), parse('.(?<=a)'), 'a')
        assert not Visitor(Unicode(), parse('.(?<=a)'), 'b')
        assert not Visitor(Unicode(), parse('.(?<!a)'), 'a')
        assert Visitor(Unicode(), parse('.(?<!a)'), 'b')
    
    def test_conditional(self):
        assert Visitor(Unicode(), parse('(.)?b(?(1)\\1)'), 'aba')
        assert not Visitor(Unicode(), parse('(.)?b(?(1)\\1)'), 'abc')
        assert Visitor(Unicode(), parse('(.)?b(?(1)\\1|c)'), 'bc')
        assert not Visitor(Unicode(), parse('(.)?b(?(1)\\1|c)'), 'bd')
        