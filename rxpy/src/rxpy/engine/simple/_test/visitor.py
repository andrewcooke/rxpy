
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

from rxpy.engine.simple.engine import SimpleEngine
from rxpy.parser.pattern import parse_pattern
from rxpy.parser.support import ParserState


def engine(parse, text, search=False):
    engine = SimpleEngine(*parse)
    return engine.run(text, search=search)


class VisitorTest(TestCase):
    
    def test_string(self):
        assert engine(parse_pattern('abc'), 'abc')
        assert engine(parse_pattern('abc'), 'abcd')
        assert not engine(parse_pattern('abc'), 'ab')
        
    def test_dot(self):
        assert engine(parse_pattern('a.c'), 'abc')
        assert engine(parse_pattern('...'), 'abcd')
        assert not engine(parse_pattern('...'), 'ab')
        assert not engine(parse_pattern('a.b'), 'a\nb')
        assert engine(parse_pattern('a.b', flags=ParserState.DOTALL), 'a\nb')
       
    def test_char(self):
        assert engine(parse_pattern('[ab]'), 'a')
        assert engine(parse_pattern('[ab]'), 'b')
        assert not engine(parse_pattern('[ab]'), 'c')

    def test_group(self):
        groups = engine(parse_pattern('(.).'), 'ab')
        assert len(groups) == 1, len(groups)
        groups = engine(parse_pattern('((.).)'), 'ab')
        assert len(groups) == 2, len(groups)
        
    def test_group_reference(self):
        assert engine(parse_pattern('(.)\\1'), 'aa')
        assert not engine(parse_pattern('(.)\\1'), 'ab')
 
    def test_split(self):
        assert engine(parse_pattern('a*b'), 'b')
        assert engine(parse_pattern('a*b'), 'ab')
        assert engine(parse_pattern('a*b'), 'aab')
        assert not engine(parse_pattern('a*b'), 'aa')
        groups = engine(parse_pattern('a*'), 'aaa')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('a*'), 'aab')
        assert len(groups[0][0]) == 2, groups[0][0]
        
    def test_nested_group(self):
        groups = engine(parse_pattern('(.)*'), 'ab')
        assert len(groups) == 1

    def test_lookahead(self):
        assert engine(parse_pattern('a(?=b)'), 'ab')
        assert not engine(parse_pattern('a(?=b)'), 'ac')
        assert not engine(parse_pattern('a(?!b)'), 'ab')
        assert engine(parse_pattern('a(?!b)'), 'ac')
    
    def test_lookback(self):
        assert engine(parse_pattern('.(?<=a)'), 'a')
        assert not engine(parse_pattern('.(?<=a)'), 'b')
        assert not engine(parse_pattern('.(?<!a)'), 'a')
        assert engine(parse_pattern('.(?<!a)'), 'b')
    
    def test_conditional(self):
        assert engine(parse_pattern('(.)?b(?(1)\\1)'), 'aba')
        assert not engine(parse_pattern('(.)?b(?(1)\\1)'), 'abc')
        assert engine(parse_pattern('(.)?b(?(1)\\1|c)'), 'bc')
        assert not engine(parse_pattern('(.)?b(?(1)\\1|c)'), 'bd')
        
    def test_star_etc(self):
        assert engine(parse_pattern('a*b'), 'b')
        assert engine(parse_pattern('a*b'), 'ab')
        assert engine(parse_pattern('a*b'), 'aab')
        assert not engine(parse_pattern('a+b'), 'b')
        assert engine(parse_pattern('a+b'), 'ab')
        assert engine(parse_pattern('a+b'), 'aab')
        assert engine(parse_pattern('a?b'), 'b')
        assert engine(parse_pattern('a?b'), 'ab')
        assert not engine(parse_pattern('a?b'), 'aab')
        
        assert engine(parse_pattern('a*b', flags=ParserState._STATEFUL), 'b')
        assert engine(parse_pattern('a*b', flags=ParserState._STATEFUL), 'ab')
        assert engine(parse_pattern('a*b', flags=ParserState._STATEFUL), 'aab')
        assert not engine(parse_pattern('a+b', flags=ParserState._STATEFUL), 'b')
        assert engine(parse_pattern('a+b', flags=ParserState._STATEFUL), 'ab')
        assert engine(parse_pattern('a+b', flags=ParserState._STATEFUL), 'aab')
        assert engine(parse_pattern('a?b', flags=ParserState._STATEFUL), 'b')
        assert engine(parse_pattern('a?b', flags=ParserState._STATEFUL), 'ab')
        assert not engine(parse_pattern('a?b', flags=ParserState._STATEFUL), 'aab')

    def test_counted(self):
        groups = engine(parse_pattern('a{2}', flags=ParserState._STATEFUL), 'aaa')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('a{1,2}', flags=ParserState._STATEFUL), 'aaa')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('a{1,}', flags=ParserState._STATEFUL), 'aaa')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('a{2}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('a{1,2}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('a{1,}?', flags=ParserState._STATEFUL), 'aaa')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('a{1,2}?b', flags=ParserState._STATEFUL), 'aab')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('a{1,}?b', flags=ParserState._STATEFUL), 'aab')
        assert len(groups[0][0]) == 3, groups[0][0]
        
        assert engine(parse_pattern('a{0,}?b', flags=ParserState._STATEFUL), 'b')
        assert engine(parse_pattern('a{0,}?b', flags=ParserState._STATEFUL), 'ab')
        assert engine(parse_pattern('a{0,}?b', flags=ParserState._STATEFUL), 'aab')
        assert not engine(parse_pattern('a{1,}?b', flags=ParserState._STATEFUL), 'b')
        assert engine(parse_pattern('a{1,}?b', flags=ParserState._STATEFUL), 'ab')
        assert engine(parse_pattern('a{1,}?b', flags=ParserState._STATEFUL), 'aab')
        assert engine(parse_pattern('a{0,1}?b', flags=ParserState._STATEFUL), 'b')
        assert engine(parse_pattern('a{0,1}?b', flags=ParserState._STATEFUL), 'ab')
        assert not engine(parse_pattern('a{0,1}?b', flags=ParserState._STATEFUL), 'aab')

        groups = engine(parse_pattern('a{2}'), 'aaa')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('a{1,2}'), 'aaa')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('a{1,}'), 'aaa')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('a{2}?'), 'aaa')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('a{1,2}?'), 'aaa')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('a{1,}?'), 'aaa')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('a{1,2}?b'), 'aab')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('a{1,}?b'), 'aab')
        assert len(groups[0][0]) == 3, groups[0][0]
        
        assert engine(parse_pattern('a{0,}?b'), 'b')
        assert engine(parse_pattern('a{0,}?b'), 'ab')
        assert engine(parse_pattern('a{0,}?b'), 'aab')
        assert not engine(parse_pattern('a{1,}?b'), 'b')
        assert engine(parse_pattern('a{1,}?b'), 'ab')
        assert engine(parse_pattern('a{1,}?b'), 'aab')
        assert engine(parse_pattern('a{0,1}?b'), 'b')
        assert engine(parse_pattern('a{0,1}?b'), 'ab')
        assert not engine(parse_pattern('a{0,1}?b'), 'aab')

    def test_ascii_escapes(self):
        groups = engine(parse_pattern('\\d*', flags=ParserState.ASCII), '12x')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('\\D*', flags=ParserState.ASCII), 'x12')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('\\w*', flags=ParserState.ASCII), '12x a')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('\\W*', flags=ParserState.ASCII), ' a')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('\\s*', flags=ParserState.ASCII), '  a')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('\\S*', flags=ParserState.ASCII), 'aa ')
        assert len(groups[0][0]) == 2, groups[0][0]
        assert engine(parse_pattern(r'a\b ', flags=ParserState.ASCII), 'a ')
        assert not engine(parse_pattern(r'a\bb', flags=ParserState.ASCII), 'ab')
        assert not engine(parse_pattern(r'a\B ', flags=ParserState.ASCII), 'a ')
        assert engine(parse_pattern(r'a\Bb', flags=ParserState.ASCII), 'ab')
        groups = engine(parse_pattern(r'\s*\b\w+\b\s*', flags=ParserState.ASCII), ' a ')
        assert groups[0][0] == ' a ', groups[0][0]
        groups = engine(parse_pattern(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._STATEFUL|ParserState.ASCII), ' a ab abc ')
        assert groups[0][0] == ' a ab abc ', groups[0][0]
        
    def test_unicode_escapes(self):
        groups = engine(parse_pattern('\\d*'), '12x')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('\\D*'), 'x12')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('\\w*'), '12x a')
        assert len(groups[0][0]) == 3, groups[0][0]
        groups = engine(parse_pattern('\\W*'), ' a')
        assert len(groups[0][0]) == 1, groups[0][0]
        groups = engine(parse_pattern('\\s*'), '  a')
        assert len(groups[0][0]) == 2, groups[0][0]
        groups = engine(parse_pattern('\\S*'), 'aa ')
        assert len(groups[0][0]) == 2, groups[0][0]
        assert engine(parse_pattern(r'a\b '), 'a ')
        assert not engine(parse_pattern(r'a\bb'), 'ab')
        assert not engine(parse_pattern(r'a\B '), 'a ')
        assert engine(parse_pattern(r'a\Bb'), 'ab')
        groups = engine(parse_pattern(r'\s*\b\w+\b\s*'), ' a ')
        assert groups[0][0] == ' a ', groups[0][0]
        groups = engine(parse_pattern(r'(\s*(\b\w+\b)\s*){3}', flags=ParserState._STATEFUL), ' a ab abc ')
        assert groups[0][0] == ' a ab abc ', groups[0][0]
    
    def test_or(self):
        assert engine(parse_pattern('a|b'), 'a')
        assert engine(parse_pattern('a|b'), 'b')
        assert not engine(parse_pattern('a|b'), 'c')
        assert engine(parse_pattern('(a|ac)$'), 'ac')

    def test_search(self):
        assert engine(parse_pattern('a'), 'ab', search=True)
        
