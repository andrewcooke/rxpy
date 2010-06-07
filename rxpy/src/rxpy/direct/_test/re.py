
from unittest import TestCase

from rxpy.direct.re import compile, escape, findall, search, sub


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
        self.assert_split(r'[^A-Za-z]+', 'Words, words, words.',
                          ['Words', 'words', 'words', ''])
        self.assert_split(r'([^A-Za-z]+)', 'Words, words, words.',
                          ['Words', ', ', 'words', ', ', 'words', '.', ''])
        self.assert_split(r'[^A-Za-z]+', 'Words, words, words.',
                          ['Words', 'words, words.'], 1)
        self.assert_split(r'\W+', 'Words, words, words.',
                          ['Words', 'words', 'words', ''])
        self.assert_split(r'(\W+)', 'Words, words, words.',
                          ['Words', ', ', 'words', ', ', 'words', '.', ''])
        self.assert_split(r'\W+', 'Words, words, words.',
                          ['Words', 'words, words.'], 1)
        
    def test_match(self):
        results = compile('.*?(x+)').match('axxb')
        assert results
        assert results.group(1) == 'xx', results.group(1)
        
    def test_findall(self):
        match = compile('(a|(b))').match('aba')
        assert match.re.groups == 2, match.re.groups
        assert match.group(0) == 'a', match.group(0)
        assert match.group(1) == 'a', match.group(1)
        assert match.group(2) == None, match.group(2)
        
        results = compile('(a|(b))').findall('aba')
        assert results == [('a', ''), ('b', 'b'), ('a', '')], results
        
        results = compile('x*').findall('a')
        assert len(results) == 2, results
        
    def test_find_from_docs(self):
        assert search(r"[a-zA-Z]+ly", 
            "He was carefully disguised but captured quickly by police.")
        results = findall(r"[a-zA-Z]+ly", 
            "He was carefully disguised but captured quickly by police.")
        assert results == ['carefully', 'quickly'], results
        results = findall(r"\w+ly", 
            "He was carefully disguised but captured quickly by police.")
        assert results == ['carefully', 'quickly'], results
        
    def test_findall_empty(self):
        results = findall('x+', 'abxd')
        assert results == ['x'], results
        results = findall('x*', 'abxd')
        # this checks against actual behaviour
        assert results == ['', '', 'x', '', ''], results

    def test_findall_sub(self):
        # this also checks against behaviour
        results = sub('x*', '-', 'abxd')
        assert results == '-a-b-d-', results
        # this too
        results = sub('x*?', '-', 'abxd')
        assert results == '-a-b-x-d-', results
        
    def test_end_of_line(self):
        results = list(compile('$').finditer('ab\n'))
        assert len(results) == 2, results
        assert results[0].group(0) == '', results[0].group(0)
        assert results[0].span(0) == (2,2), results[0].span(0)
        assert results[1].group(0) == '', results[1].group(0)
        assert results[1].span(0) == (3,3), results[1].span(0)
        
        results = sub('$', 'x', 'ab\n')
        assert results == 'abx\nx', results


class EscapeTest(TestCase):
    
    def test_escape(self):
        text = '123abc;.,}{? '
        esc = escape('123abc;.,}{? ')
        assert esc == '123abc\\;\\.\\,\\}\\{\\?\\ ', esc
        result = compile(esc).match(text)
        assert result

