
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
        