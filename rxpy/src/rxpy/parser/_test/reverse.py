
from unittest import TestCase

from re import compile


class EscapeTest(TestCase):
    
    def test_literal_escape(self):
        '''
        This shows that the regexp interpreter itself expands literal escape
        characters.
        '''
        p = compile('a\\x62c')
        assert p.match('abc')
        assert not p.match('axc')
        assert p.match('a\x62c')
        
    def test_escape(self):
        '''
        Alternatively, the character can be simply used
        '''
        p = compile('a\x62c')
        assert p.match('abc')
        assert not p.match('axc')
        assert p.match('a\x62c')

    def test_slash_escape(self):
        '''
        See http://groups.google.com/group/comp.lang.python/browse_thread/thread/3a27b819307c0cb6#
        '''
        p = compile('a\\\x62c')
#        assert p.match('a\\bc')

    def test_nested_groups(self):
        p = compile('(.)*')
        m = p.match('ab')
        assert m
        assert m.groups() == ('b',), m.groups()
        assert m.group(0) == 'ab', m.group(0)
        assert m.group(1) == 'b', m.group(1)
        
        p = compile(r'(?:\s*(\b\w+\b)\s*){3}')
        m = p.match('foo bar baz ')
        assert m
        assert m.groups() == ('baz',), m.groups()
        
        p = compile(r'(?:\s*(\b\w*\b)\s*){3}')
        m = p.match(' a ab abc ')
        assert m.group(0) == ' a ab abc ', m.group(0)
        
#        p = compile('(\b.*?\b)*')
#        m = p.match(' a  ab  abc ')
#        assert m.groups() == ('abc'), m.groups()
        