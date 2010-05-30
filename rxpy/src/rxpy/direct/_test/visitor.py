
from unittest import TestCase

from rxpy.alphabet.unicode import Unicode
from rxpy.direct.visitor import Visitor
from rxpy.parser._test.parser import parse
from rxpy.parser.parser import ParserState
from rxpy.alphabet.ascii import Ascii


class VisitorTest(TestCase):
    
    def test_string(self):
        assert Visitor(parse('abc'), 'abc')
        assert Visitor(parse('abc'), 'abcd')
        assert not Visitor(parse('abc'), 'ab')
        
    def test_dot(self):
        assert Visitor(parse('a.c'), 'abc')
        assert Visitor(parse('...'), 'abcd')
        assert not Visitor(parse('...'), 'ab')
        
    def test_char(self):
        assert Visitor(parse('[ab]'), 'a')
        assert Visitor(parse('[ab]'), 'b')
        assert not Visitor(parse('[ab]'), 'c')

    def test_group(self):
        v = Visitor(parse('(.).'), 'ab')
        assert len(v.groups) == 1, len(v.groups)
        v = Visitor(parse('((.).)'), 'ab')
        assert len(v.groups) == 2, len(v.groups)
        
    def test_group_reference(self):
        assert Visitor(parse('(.)\\1'), 'aa')
        assert not Visitor(parse('(.)\\1'), 'ab')
 
    def test_split(self):
        assert Visitor(parse('a*b'), 'b')
        assert Visitor(parse('a*b'), 'ab')
        assert Visitor(parse('a*b'), 'aab')
        assert not Visitor(parse('a*b'), 'aa')
        v = Visitor(parse('a*'), 'aaa')
        assert len(v.groups[0]) == 3, v.groups[0]
        v = Visitor(parse('a*'), 'aab')
        assert len(v.groups[0]) == 2, v.groups[0]
        
    def test_nested_group(self):
        v = Visitor(parse('(.)*'), 'ab')
        assert len(v.groups) == 1

    def test_lookahead(self):
        assert Visitor(parse('a(?=b)'), 'ab')
        assert not Visitor(parse('a(?=b)'), 'ac')
        assert not Visitor(parse('a(?!b)'), 'ab')
        assert Visitor(parse('a(?!b)'), 'ac')
    
    def test_lookback(self):
        assert Visitor(parse('.(?<=a)'), 'a')
        assert not Visitor(parse('.(?<=a)'), 'b')
        assert not Visitor(parse('.(?<!a)'), 'a')
        assert Visitor(parse('.(?<!a)'), 'b')
    
    def test_conditional(self):
        assert Visitor(parse('(.)?b(?(1)\\1)'), 'aba')
        assert not Visitor(parse('(.)?b(?(1)\\1)'), 'abc')
        assert Visitor(parse('(.)?b(?(1)\\1|c)'), 'bc')
        assert not Visitor(parse('(.)?b(?(1)\\1|c)'), 'bd')
        
    def test_counted(self):
        v = Visitor(parse('a{2}', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('a{1,2}', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('a{1,}', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0]) == 3, v.groups[0]
        v = Visitor(parse('a{2}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('a{1,2}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0]) == 1, v.groups[0]
        v = Visitor(parse('a{1,}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0]) == 1, v.groups[0]
        v = Visitor(parse('a{1,2}?b', flags=ParserState._STATEFUL), 'aab')
        assert len(v.groups[0]) == 3, v.groups[0]
        v = Visitor(parse('a{1,}?b', flags=ParserState._STATEFUL), 'aab')
        assert len(v.groups[0]) == 3, v.groups[0]

    def test_ascii_escapes(self):
        v = Visitor(parse('\\d*', flags=ParserState.ASCII), '12x')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('\\D*', flags=ParserState.ASCII), 'x12')
        assert len(v.groups[0]) == 1, v.groups[0]
        v = Visitor(parse('\\w*', flags=ParserState.ASCII), '12x a')
        assert len(v.groups[0]) == 3, v.groups[0]
        v = Visitor(parse('\\W*', flags=ParserState.ASCII), ' a')
        assert len(v.groups[0]) == 1, v.groups[0]
        v = Visitor(parse('\\s*', flags=ParserState.ASCII), '  a')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('\\S*', flags=ParserState.ASCII), 'aa ')
        assert len(v.groups[0]) == 2, v.groups[0]
        assert Visitor(parse(r'a\b ', flags=ParserState.ASCII), 'a ')
        assert not Visitor(parse(r'a\bb', flags=ParserState.ASCII), 'ab')
        assert not Visitor(parse(r'a\B ', flags=ParserState.ASCII), 'a ')
        assert Visitor(parse(r'a\Bb', flags=ParserState.ASCII), 'ab')
        v = Visitor(parse(r'\s*\b\w+\b\s*', flags=ParserState.ASCII), ' a ')
        assert v.groups[0] == ' a ', v.groups[0]
        v = Visitor(parse(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._STATEFUL|ParserState.ASCII), ' a ab abc ')
        assert v.groups[0] == ' a ab abc ', v.groups[0]
        
    def test_unicode_escapes(self):
        v = Visitor(parse('\\d*'), '12x')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('\\D*'), 'x12')
        assert len(v.groups[0]) == 1, v.groups[0]
        v = Visitor(parse('\\w*'), '12x a')
        assert len(v.groups[0]) == 3, v.groups[0]
        v = Visitor(parse('\\W*'), ' a')
        assert len(v.groups[0]) == 1, v.groups[0]
        v = Visitor(parse('\\s*'), '  a')
        assert len(v.groups[0]) == 2, v.groups[0]
        v = Visitor(parse('\\S*'), 'aa ')
        assert len(v.groups[0]) == 2, v.groups[0]
        assert Visitor(parse(r'a\b '), 'a ')
        assert not Visitor(parse(r'a\bb'), 'ab')
        assert not Visitor(parse(r'a\B '), 'a ')
        assert Visitor(parse(r'a\Bb'), 'ab')
        v = Visitor(parse(r'\s*\b\w+\b\s*'), ' a ')
        assert v.groups[0] == ' a ', v.groups[0]
        v = Visitor(parse(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._STATEFUL), ' a ab abc ')
        assert v.groups[0] == ' a ab abc ', v.groups[0]
        