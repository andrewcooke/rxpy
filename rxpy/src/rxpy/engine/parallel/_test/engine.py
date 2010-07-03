
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

from rxpy.engine.parallel.engine import ParallelEngine
from rxpy.parser.pattern import parse_pattern
from rxpy.parser.support import ParserState


def engine(parse, text, search=False, ticks=None, maxdepth=None):
    engine = ParallelEngine(*parse)
    results = engine.run(text, search=search)
    if ticks:
        assert engine.ticks == ticks, engine.ticks
    if maxdepth:
        assert engine.maxdepth == maxdepth, engine.maxdepth
    return results

def parse(pattern, flags=0):
    return parse_pattern(pattern, ParallelEngine, flags=flags)


class EngineTest(TestCase):
    
    def test_string(self):
        assert engine(parse('abc'), 'abc')
        assert engine(parse('abc'), 'abcd')
        assert not engine(parse('abc'), 'ab')
        
    def test_dot(self):
        assert engine(parse('a.c'), 'abc')
        assert engine(parse('...'), 'abcd')
        assert not engine(parse('...'), 'ab')
        assert not engine(parse('a.b'), 'a\nb')
        assert engine(parse('a.b', flags=ParserState.DOTALL), 'a\nb')
       
    def test_char(self):
        assert engine(parse('[ab]'), 'a')
        assert engine(parse('[ab]'), 'b')
        assert not engine(parse('[ab]'), 'c')

    def test_group(self):
        groups = engine(parse('(.).'), 'ab')
        assert len(groups) == 1, len(groups)
        groups = engine(parse('((.).)'), 'ab')
        assert len(groups) == 2, len(groups)
        
    def test_group_reference(self):
        assert engine(parse('(.)\\1'), 'aa')
        assert not engine(parse('(.)\\1'), 'ab')
 
    def test_split(self):
        assert engine(parse('a*b'), 'b')
        assert engine(parse('a*b'), 'ab')
        assert engine(parse('a*b'), 'aab')
        assert not engine(parse('a*b'), 'aa')
        groups = engine(parse('a*'), 'aaa')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('a*'), 'aab')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        assert engine(parse('a*'), 'a')
        assert engine(parse('a*'), 'aa')
        assert engine(parse('a*'), '')
        assert engine(parse('a+'), 'a')
        assert engine(parse('a+'), 'aa')
        assert not engine(parse('a+'), '')
        
    def test_nested_group(self):
        groups = engine(parse('(.)*'), 'ab')
        assert len(groups) == 1

    def test_lookahead(self):
        assert engine(parse('a(?=b)'), 'ab')
        assert not engine(parse('a(?=b)'), 'ac')
        assert not engine(parse('a(?!b)'), 'ab')
        assert engine(parse('a(?!b)'), 'ac')
    
    def test_lookback(self):
        assert engine(parse('.(?<=a)'), 'a')
        assert not engine(parse('.(?<=a)'), 'b')
        assert not engine(parse('.(?<!a)'), 'a')
        assert engine(parse('.(?<!a)'), 'b')
    
    def test_lookback_with_offset(self):
        assert engine(parse('..(?<=a)'), 'xa', ticks=7)
        assert not engine(parse('..(?<=a)'), 'ax')
        
    def test_lookback_optimisations(self):
        assert engine(parse('(.).(?<=a)'), 'xa', ticks=9)
        # only one more tick with an extra character because we avoid starting
        # from the start in this case
        assert engine(parse('.(.).(?<=a)'), 'xxa', ticks=10)
        
        assert engine(parse('(.).(?<=\\1)'), 'aa', ticks=10)
        # again, just one tick more
        assert engine(parse('.(.).(?<=\\1)'), 'xaa', ticks=11)
        assert not engine(parse('.(.).(?<=\\1)'), 'xxa')
        
        assert engine(parse('(.).(?<=(\\1))'), 'aa', ticks=17)
        # but here, three ticks more because we have a group reference with
        # changing groups, so can't reliably calculate lookback distance
        assert engine(parse('.(.).(?<=(\\1))'), 'xaa', ticks=21)
        assert not engine(parse('.(.).(?<=(\\1))'), 'xxa')
        
    def test_lookback_bug_1(self):
        result = engine(parse('.*(?<!abc)(d.f)'), 'abcdefdof')
        assert result.group(1) == 'dof', result.group(1)
        result = engine(parse('(?<!abc)(d.f)'), 'abcdefdof', search=True)
        assert result.group(1) == 'dof', result.group(1)
        
    def test_lookback_bug_2(self):
        assert not engine(parse(r'.*(?<=\bx)a'), 'xxa')
        assert engine(parse(r'.*(?<!\bx)a'), 'xxa')
        assert not engine(parse(r'.*(?<!\Bx)a'), 'xxa')
        assert engine(parse(r'.*(?<=\Bx)a'), 'xxa')
    
    def test_conditional(self):
        assert engine(parse('(.)?b(?(1)\\1)'), 'aba')
        assert not engine(parse('(.)?b(?(1)\\1)'), 'abc')
        assert engine(parse('(.)?b(?(1)\\1|c)'), 'bc')
        assert not engine(parse('(.)?b(?(1)\\1|c)'), 'bd')
        
    def test_star_etc(self):
        assert engine(parse('a*b'), 'b')
        assert engine(parse('a*b'), 'ab')
        assert engine(parse('a*b'), 'aab')
        assert not engine(parse('a+b'), 'b')
        assert engine(parse('a+b'), 'ab')
        assert engine(parse('a+b'), 'aab')
        assert engine(parse('a?b'), 'b')
        assert engine(parse('a?b'), 'ab')
        assert not engine(parse('a?b'), 'aab')
        
        assert engine(parse('a*b', flags=ParserState._LOOPS), 'b')
        assert engine(parse('a*b', flags=ParserState._LOOPS), 'ab')
        assert engine(parse('a*b', flags=ParserState._LOOPS), 'aab')
        assert not engine(parse('a+b', flags=ParserState._LOOPS), 'b')
        assert engine(parse('a+b', flags=ParserState._LOOPS), 'ab')
        assert engine(parse('a+b', flags=ParserState._LOOPS), 'aab')
        assert engine(parse('a?b', flags=ParserState._LOOPS), 'b')
        assert engine(parse('a?b', flags=ParserState._LOOPS), 'ab')
        assert not engine(parse('a?b', flags=ParserState._LOOPS), 'aab')

    def test_counted(self):
        groups = engine(parse('a{2}', flags=ParserState._LOOPS), 'aaa')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('a{1,2}', flags=ParserState._LOOPS), 'aaa')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('a{1,}', flags=ParserState._LOOPS), 'aaa')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('a{2}?', flags=ParserState._LOOPS), 'aaa')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('a{1,2}?', flags=ParserState._LOOPS), 'aaa')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('a{1,}?', flags=ParserState._LOOPS), 'aaa')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('a{1,2}?b', flags=ParserState._LOOPS), 'aab')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('a{1,}?b', flags=ParserState._LOOPS), 'aab')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        
        assert engine(parse('a{0,}?b', flags=ParserState._LOOPS), 'b')
        assert engine(parse('a{0,}?b', flags=ParserState._LOOPS), 'ab')
        assert engine(parse('a{0,}?b', flags=ParserState._LOOPS), 'aab')
        assert not engine(parse('a{1,}?b', flags=ParserState._LOOPS), 'b')
        assert engine(parse('a{1,}?b', flags=ParserState._LOOPS), 'ab')
        assert engine(parse('a{1,}?b', flags=ParserState._LOOPS), 'aab')
        assert engine(parse('a{0,1}?b', flags=ParserState._LOOPS), 'b')
        assert engine(parse('a{0,1}?b', flags=ParserState._LOOPS), 'ab')
        assert not engine(parse('a{0,1}?b', flags=ParserState._LOOPS), 'aab')

        groups = engine(parse('a{2}'), 'aaa')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('a{1,2}'), 'aaa')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('a{1,}'), 'aaa')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('a{2}?'), 'aaa')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('a{1,2}?'), 'aaa')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('a{1,}?'), 'aaa')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('a{1,2}?b'), 'aab')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('a{1,}?b'), 'aab')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        
        assert engine(parse('a{0,}?b'), 'b')
        assert engine(parse('a{0,}?b'), 'ab')
        assert engine(parse('a{0,}?b'), 'aab')
        assert not engine(parse('a{1,}?b'), 'b')
        assert engine(parse('a{1,}?b'), 'ab')
        assert engine(parse('a{1,}?b'), 'aab')
        assert engine(parse('a{0,1}?b'), 'b')
        assert engine(parse('a{0,1}?b'), 'ab')
        assert not engine(parse('a{0,1}?b'), 'aab')

    def test_ascii_escapes(self):
        groups = engine(parse('\\d*', flags=ParserState.ASCII), '12x')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('\\D*', flags=ParserState.ASCII), 'x12')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('\\w*', flags=ParserState.ASCII), '12x a')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('\\W*', flags=ParserState.ASCII), ' a')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('\\s*', flags=ParserState.ASCII), '  a')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('\\S*', flags=ParserState.ASCII), 'aa ')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        assert engine(parse(r'a\b ', flags=ParserState.ASCII), 'a ')
        assert not engine(parse(r'a\bb', flags=ParserState.ASCII), 'ab')
        assert not engine(parse(r'a\B ', flags=ParserState.ASCII), 'a ')
        assert engine(parse(r'a\Bb', flags=ParserState.ASCII), 'ab')
        groups = engine(parse(r'\s*\b\w+\b\s*', flags=ParserState.ASCII), ' a ')
        assert groups.data(0)[0] == ' a ', groups.data(0)[0]
        groups = engine(parse(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._LOOPS|ParserState.ASCII), ' a ab abc ')
        assert groups.data(0)[0] == ' a ab abc ', groups.data(0)[0]
        
    def test_unicode_escapes(self):
        groups = engine(parse('\\d*'), '12x')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('\\D*'), 'x12')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('\\w*'), '12x a')
        assert len(groups.data(0)[0]) == 3, groups.data(0)[0]
        groups = engine(parse('\\W*'), ' a')
        assert len(groups.data(0)[0]) == 1, groups.data(0)[0]
        groups = engine(parse('\\s*'), '  a')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        groups = engine(parse('\\S*'), 'aa ')
        assert len(groups.data(0)[0]) == 2, groups.data(0)[0]
        assert engine(parse(r'a\b '), 'a ')
        assert not engine(parse(r'a\bb'), 'ab')
        assert not engine(parse(r'a\B '), 'a ')
        assert engine(parse(r'a\Bb'), 'ab')
        groups = engine(parse(r'\s*\b\w+\b\s*'), ' a ')
        assert groups.data(0)[0] == ' a ', groups.data(0)[0]
        groups = engine(parse(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._LOOPS), ' a ab abc ')
        assert groups.data(0)[0] == ' a ab abc ', groups.data(0)[0]
    
    def test_or(self):
        assert engine(parse('a|b'), 'a')
        assert engine(parse('a|b'), 'b')
        assert not engine(parse('a|b'), 'c')
        assert engine(parse('(a|ac)'), 'ac')
        assert engine(parse('(a|ac)$'), 'ac')

    def test_search(self):
#        assert engine(parse('a'), 'ab', search=True)
#        assert engine(parse('$'), '', search=True)
        assert engine(parse('$'), 'a', search=True)
        
    def test_end_of_line(self):
        assert engine(parse('ab$'), 'ab')
        assert engine(parse('ab$'), 'ab\n')
        assert not engine(parse('ab$'), 'abc')
        assert not engine(parse('ab$'), 'ab\nc')
        assert engine(parse('(?m)ab$'), 'ab\nc')
        
        