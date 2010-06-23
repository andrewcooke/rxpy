
# The contents of this file are subject to the Mozilla Public License
# (MPL) Version 1.1 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License
# at http://www.mozilla.org/MPL/                                      
#                                                                     
# Software distributed under the License is distributed on an "AS IS" 
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See 
# the License for the specific language governing rights and          
# limitations under the License.                                      
#                                                                     
# The Original Code is RXPY (http://www.acooke.org/rxpy)              
# The Initial Developer of the Original Code is Andrew Cooke.         
# Portions created by the Initial Developer are Copyright (C) 2010
# Andrew Cooke (andrew@acooke.org). All Rights Reserved.               
#                                                                      
# Alternatively, the contents of this file may be used under the terms 
# of the LGPL license (the GNU Lesser General Public License,          
# http://www.gnu.org/licenses/lgpl.html), in which case the provisions 
# of the LGPL License are applicable instead of those above.           
#                                                                      
# If you wish to allow use of your version of this file only under the 
# terms of the LGPL License and not to allow others to use your version
# of this file under the MPL, indicate your decision by deleting the   
# provisions above and replace them with the notice and other provisions
# required by the LGPL License.  If you do not delete the provisions    
# above, a recipient may use your version of this file under either the 
# MPL or the LGPL License.                                              


from unittest import TestCase

from rxpy.direct.re import compile, escape, findall, search, sub
from rxpy.parser.parser import ParserState


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


class SubStringsTest(TestCase):
    
    def test_types(self):
        for pattern in ('.', 'a', u'u'):
            for text in ('a', 'u', u'a', u'u'):
                for repl in ('A', u'U'):
                    for flags in (0, ParserState.ASCII, ParserState.UNICODE):
                        s = sub(pattern, repl, text, flags=flags)
                        print(pattern, text, repl, flags, s)
                        if flags:
                            if flags == ParserState.ASCII and type(text) == str:
                                assert type(s) == str, type(s)
                            else:   
                                assert type(s) == unicode, type(s)
                        else:
                            if type(text) == str and type(pattern) == str:
                                assert type(s) == str, type(s)
                            else:   
                                assert type(s) == unicode, type(s)

