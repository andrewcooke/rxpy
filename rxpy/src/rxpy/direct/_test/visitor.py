
from unittest import TestCase

from rxpy.direct.visitor import Visitor
from rxpy.parser._test.parser import parse
from rxpy.parser.parser import ParserState


class VisitorTest(TestCase):
    
    def test_string(self):
        assert Visitor.from_parse_results(parse('abc'), 'abc')
        assert Visitor.from_parse_results(parse('abc'), 'abcd')
        assert not Visitor.from_parse_results(parse('abc'), 'ab')
        
    def test_dot(self):
        assert Visitor.from_parse_results(parse('a.c'), 'abc')
        assert Visitor.from_parse_results(parse('...'), 'abcd')
        assert not Visitor.from_parse_results(parse('...'), 'ab')
        assert not Visitor.from_parse_results(parse('a.b'), 'a\nb')
        assert Visitor.from_parse_results(parse('a.b', flags=ParserState.DOTALL), 'a\nb')
       
    def test_char(self):
        assert Visitor.from_parse_results(parse('[ab]'), 'a')
        assert Visitor.from_parse_results(parse('[ab]'), 'b')
        assert not Visitor.from_parse_results(parse('[ab]'), 'c')

    def test_group(self):
        v = Visitor.from_parse_results(parse('(.).'), 'ab')
        assert len(v.groups) == 1, len(v.groups)
        v = Visitor.from_parse_results(parse('((.).)'), 'ab')
        assert len(v.groups) == 2, len(v.groups)
        
    def test_group_reference(self):
        assert Visitor.from_parse_results(parse('(.)\\1'), 'aa')
        assert not Visitor.from_parse_results(parse('(.)\\1'), 'ab')
 
    def test_split(self):
        assert Visitor.from_parse_results(parse('a*b'), 'b')
        assert Visitor.from_parse_results(parse('a*b'), 'ab')
        assert Visitor.from_parse_results(parse('a*b'), 'aab')
        assert not Visitor.from_parse_results(parse('a*b'), 'aa')
        v = Visitor.from_parse_results(parse('a*'), 'aaa')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a*'), 'aab')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        
    def test_nested_group(self):
        v = Visitor.from_parse_results(parse('(.)*'), 'ab')
        assert len(v.groups) == 1

    def test_lookahead(self):
        assert Visitor.from_parse_results(parse('a(?=b)'), 'ab')
        assert not Visitor.from_parse_results(parse('a(?=b)'), 'ac')
        assert not Visitor.from_parse_results(parse('a(?!b)'), 'ab')
        assert Visitor.from_parse_results(parse('a(?!b)'), 'ac')
    
    def test_lookback(self):
        assert Visitor.from_parse_results(parse('.(?<=a)'), 'a')
        assert not Visitor.from_parse_results(parse('.(?<=a)'), 'b')
        assert not Visitor.from_parse_results(parse('.(?<!a)'), 'a')
        assert Visitor.from_parse_results(parse('.(?<!a)'), 'b')
    
    def test_conditional(self):
        assert Visitor.from_parse_results(parse('(.)?b(?(1)\\1)'), 'aba')
        assert not Visitor.from_parse_results(parse('(.)?b(?(1)\\1)'), 'abc')
        assert Visitor.from_parse_results(parse('(.)?b(?(1)\\1|c)'), 'bc')
        assert not Visitor.from_parse_results(parse('(.)?b(?(1)\\1|c)'), 'bd')
        
    def test_star_etc(self):
        assert Visitor.from_parse_results(parse('a*b'), 'b')
        assert Visitor.from_parse_results(parse('a*b'), 'ab')
        assert Visitor.from_parse_results(parse('a*b'), 'aab')
        assert not Visitor.from_parse_results(parse('a+b'), 'b')
        assert Visitor.from_parse_results(parse('a+b'), 'ab')
        assert Visitor.from_parse_results(parse('a+b'), 'aab')
        assert Visitor.from_parse_results(parse('a?b'), 'b')
        assert Visitor.from_parse_results(parse('a?b'), 'ab')
        assert not Visitor.from_parse_results(parse('a?b'), 'aab')
        
        assert Visitor.from_parse_results(parse('a*b', flags=ParserState._STATEFUL), 'b')
        assert Visitor.from_parse_results(parse('a*b', flags=ParserState._STATEFUL), 'ab')
        assert Visitor.from_parse_results(parse('a*b', flags=ParserState._STATEFUL), 'aab')
        assert not Visitor.from_parse_results(parse('a+b', flags=ParserState._STATEFUL), 'b')
        assert Visitor.from_parse_results(parse('a+b', flags=ParserState._STATEFUL), 'ab')
        assert Visitor.from_parse_results(parse('a+b', flags=ParserState._STATEFUL), 'aab')
        assert Visitor.from_parse_results(parse('a?b', flags=ParserState._STATEFUL), 'b')
        assert Visitor.from_parse_results(parse('a?b', flags=ParserState._STATEFUL), 'ab')
        assert not Visitor.from_parse_results(parse('a?b', flags=ParserState._STATEFUL), 'aab')

    def test_counted(self):
        v = Visitor.from_parse_results(parse('a{2}', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,2}', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,}', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{2}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,2}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,2}?b', flags=ParserState._STATEFUL), 'aab')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,}?b', flags=ParserState._STATEFUL), 'aab')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        
        assert Visitor.from_parse_results(parse('a{0,}?b', flags=ParserState._STATEFUL), 'b')
        assert Visitor.from_parse_results(parse('a{0,}?b', flags=ParserState._STATEFUL), 'ab')
        assert Visitor.from_parse_results(parse('a{0,}?b', flags=ParserState._STATEFUL), 'aab')
        assert not Visitor.from_parse_results(parse('a{1,}?b', flags=ParserState._STATEFUL), 'b')
        assert Visitor.from_parse_results(parse('a{1,}?b', flags=ParserState._STATEFUL), 'ab')
        assert Visitor.from_parse_results(parse('a{1,}?b', flags=ParserState._STATEFUL), 'aab')
        assert Visitor.from_parse_results(parse('a{0,1}?b', flags=ParserState._STATEFUL), 'b')
        assert Visitor.from_parse_results(parse('a{0,1}?b', flags=ParserState._STATEFUL), 'ab')
        assert not Visitor.from_parse_results(parse('a{0,1}?b', flags=ParserState._STATEFUL), 'aab')

        v = Visitor.from_parse_results(parse('a{2}'), 'aaa')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,2}'), 'aaa')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,}'), 'aaa')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{2}?'), 'aaa')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,2}?'), 'aaa')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,}?'), 'aaa')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,2}?b'), 'aab')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('a{1,}?b'), 'aab')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        
        assert Visitor.from_parse_results(parse('a{0,}?b'), 'b')
        assert Visitor.from_parse_results(parse('a{0,}?b'), 'ab')
        assert Visitor.from_parse_results(parse('a{0,}?b'), 'aab')
        assert not Visitor.from_parse_results(parse('a{1,}?b'), 'b')
        assert Visitor.from_parse_results(parse('a{1,}?b'), 'ab')
        assert Visitor.from_parse_results(parse('a{1,}?b'), 'aab')
        assert Visitor.from_parse_results(parse('a{0,1}?b'), 'b')
        assert Visitor.from_parse_results(parse('a{0,1}?b'), 'ab')
        assert not Visitor.from_parse_results(parse('a{0,1}?b'), 'aab')

    def test_ascii_escapes(self):
        v = Visitor.from_parse_results(parse('\\d*', flags=ParserState.ASCII), '12x')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\D*', flags=ParserState.ASCII), 'x12')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\w*', flags=ParserState.ASCII), '12x a')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\W*', flags=ParserState.ASCII), ' a')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\s*', flags=ParserState.ASCII), '  a')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\S*', flags=ParserState.ASCII), 'aa ')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        assert Visitor.from_parse_results(parse(r'a\b ', flags=ParserState.ASCII), 'a ')
        assert not Visitor.from_parse_results(parse(r'a\bb', flags=ParserState.ASCII), 'ab')
        assert not Visitor.from_parse_results(parse(r'a\B ', flags=ParserState.ASCII), 'a ')
        assert Visitor.from_parse_results(parse(r'a\Bb', flags=ParserState.ASCII), 'ab')
        v = Visitor.from_parse_results(parse(r'\s*\b\w+\b\s*', flags=ParserState.ASCII), ' a ')
        assert v.groups[0][0] == ' a ', v.groups[0][0]
        v = Visitor.from_parse_results(parse(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._STATEFUL|ParserState.ASCII), ' a ab abc ')
        assert v.groups[0][0] == ' a ab abc ', v.groups[0][0]
        
    def test_unicode_escapes(self):
        v = Visitor.from_parse_results(parse('\\d*'), '12x')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\D*'), 'x12')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\w*'), '12x a')
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\W*'), ' a')
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\s*'), '  a')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(parse('\\S*'), 'aa ')
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        assert Visitor.from_parse_results(parse(r'a\b '), 'a ')
        assert not Visitor.from_parse_results(parse(r'a\bb'), 'ab')
        assert not Visitor.from_parse_results(parse(r'a\B '), 'a ')
        assert Visitor.from_parse_results(parse(r'a\Bb'), 'ab')
        v = Visitor.from_parse_results(parse(r'\s*\b\w+\b\s*'), ' a ')
        assert v.groups[0][0] == ' a ', v.groups[0][0]
        v = Visitor.from_parse_results(parse(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._STATEFUL), ' a ab abc ')
        assert v.groups[0][0] == ' a ab abc ', v.groups[0][0]
    
    def test_or(self):
        assert Visitor.from_parse_results(parse('a|b'), 'a')
        assert Visitor.from_parse_results(parse('a|b'), 'b')
        assert not Visitor.from_parse_results(parse('a|b'), 'c')
        assert not Visitor.from_parse_results(parse('(a|ac)$'), 'ac')
        assert Visitor.from_parse_results(parse('a|b', flags=ParserState._BACKTRACK_OR), 'a')
        assert Visitor.from_parse_results(parse('a|b', flags=ParserState._BACKTRACK_OR), 'b')
        assert not Visitor.from_parse_results(parse('a|b', flags=ParserState._BACKTRACK_OR), 'c')
        assert Visitor.from_parse_results(parse('(a|ac)$', flags=ParserState._BACKTRACK_OR), 'ac')

    def test_search(self):
        assert Visitor.from_parse_results(parse('a'), 'ab', search=True)
        
