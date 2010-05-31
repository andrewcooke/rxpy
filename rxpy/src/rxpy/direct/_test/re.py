
from unittest import TestCase

from rxpy.direct.re import compile


class GroupsTest(TestCase):
    
    def assert_groups(self, pattern, text, groups, target):
        try:
            results = compile(pattern).match(text).group(*groups)
            assert results == target, repr(results)
        except Exception, e:
            if isinstance(target, type):
                assert isinstance(e, target), repr(e)
            else:
                assert False, repr(e)
    
    def test_zero(self):
        self.assert_groups('.*', 'abc', [], 'abc')
        self.assert_groups('.*', 'abc', [0], 'abc')
        self.assert_groups('.(.).', 'abc', [], 'abc')
        self.assert_groups('.(.).', 'abc', [0], 'abc')
    
    def test_numbered(self):
        self.assert_groups('.(.).', 'abc', [1], 'b')
        self.assert_groups('.(.)*', 'abc', [1], 'c')
        self.assert_groups('.(.).(.?)', 'abc', [2], '')
        self.assert_groups('.(.).(.)?', 'abc', [2], None)
        self.assert_groups('.(.).(.?)', 'abc', [3], IndexError)


class RegexObjectTest(TestCase):
    
    def assert_split(self, pattern, text, target, *args):
        result = compile(pattern).split(text, *args)
        assert result == target, result
    
    def test_split_from_docs(self):
        self.assert_split(r'\W+', 'Words, words, words.',
                          ['Words', 'words', 'words', ''])
        self.assert_split(r'(\W+)', 'Words, words, words.'
                          ['Words', ', ', 'words', ', ', 'words', '.', ''])
        self.assert_split(r'\W+', 'Words, words, words.',
                          ['Words', 'words, words.'], 1)
