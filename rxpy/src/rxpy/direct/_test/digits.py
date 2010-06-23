
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

from rxpy.alphabet.digits import Digits
from rxpy.direct.visitor import Visitor
from rxpy.parser._test.parser import parse
from rxpy.parser.parser import ParserState, RxpyException
from rxpy.lib import UnsupportedOperation


class VisitorTest(TestCase):
    
    def parse(self, regexp, flags=0):
        return parse(regexp, alphabet=Digits(), flags=flags)
    
    def test_string(self):
        assert Visitor.from_parse_results(self.parse('1'), [1])
        assert Visitor.from_parse_results(self.parse('123'), [1,2,3])
        assert Visitor.from_parse_results(self.parse('123'), [1,2,3,4])
        assert not Visitor.from_parse_results(self.parse('123'), [1,2])
        
    def test_dot(self):
        assert Visitor.from_parse_results(self.parse('1.3'), [1,2,3])
        assert Visitor.from_parse_results(self.parse('...'), [1,2,3,4])
        assert not Visitor.from_parse_results(self.parse('...'), [1,2])
        assert not Visitor.from_parse_results(self.parse('1.2'), [1,None,2])
        assert not Visitor.from_parse_results(self.parse('1.2', flags=ParserState.DOTALL), [1,None,2])
       
    def test_char(self):
        assert Visitor.from_parse_results(self.parse('[12]'), [1])
        assert Visitor.from_parse_results(self.parse('[12]'), [2])
        assert not Visitor.from_parse_results(self.parse('[12]'), [3])

    def test_group(self):
        v = Visitor.from_parse_results(self.parse('(.).'), [1,2])
        assert len(v.groups) == 1, len(v.groups)
        v = Visitor.from_parse_results(self.parse('((.).)'), [1,2])
        assert len(v.groups) == 2, len(v.groups)
        
    def test_group_reference(self):
        assert Visitor.from_parse_results(self.parse('(.)\\1'), [1,1])
        assert not Visitor.from_parse_results(self.parse('(.)\\1'), [1,2])
 
    def test_split(self):
        assert Visitor.from_parse_results(self.parse('1*2'), [2])
        assert Visitor.from_parse_results(self.parse('1*2'), [1,2])
        assert Visitor.from_parse_results(self.parse('1*2'), [1,1,2])
        assert not Visitor.from_parse_results(self.parse('1*2'), [1,1])
        v = Visitor.from_parse_results(self.parse('1*'), [1,1,1])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1*'), [1,1,2])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        
    def test_nested_group(self):
        v = Visitor.from_parse_results(self.parse('(.)*'), [1,2])
        assert len(v.groups) == 1

    def test_lookahead(self):
        assert Visitor.from_parse_results(self.parse('1(?=2)'), [1,2])
        assert not Visitor.from_parse_results(self.parse('1(?=2)'), [1,3])
        assert not Visitor.from_parse_results(self.parse('1(?!2)'), [1,2])
        assert Visitor.from_parse_results(self.parse('1(?!2)'), [1,3])
    
    def test_lookback(self):
        assert Visitor.from_parse_results(self.parse('.(?<=1)'), [1])
        assert not Visitor.from_parse_results(self.parse('.(?<=1)'), [2])
        assert not Visitor.from_parse_results(self.parse('.(?<!1)'), [1])
        assert Visitor.from_parse_results(self.parse('.(?<!1)'), [2])
    
    def test_conditional(self):
        assert Visitor.from_parse_results(self.parse('(.)?2(?(1)\\1)'), [1,2,1])
        assert not Visitor.from_parse_results(self.parse('(.)?2(?(1)\\1)'), [1,2,3])
        assert Visitor.from_parse_results(self.parse('(.)?2(?(1)\\1|3)'), [2,3])
        assert not Visitor.from_parse_results(self.parse('(.)?2(?(1)\\1|3)'), [2,4])
        
    def test_star_etc(self):
        assert Visitor.from_parse_results(self.parse('1*2'), [2])
        assert Visitor.from_parse_results(self.parse('1*2'), [1,2])
        assert Visitor.from_parse_results(self.parse('1*2'), [1,1,2])
        assert not Visitor.from_parse_results(self.parse('1+2'), [2])
        assert Visitor.from_parse_results(self.parse('1+2'), [1,2])
        assert Visitor.from_parse_results(self.parse('1+2'), [1,1,2])
        assert Visitor.from_parse_results(self.parse('1?2'), [2])
        assert Visitor.from_parse_results(self.parse('1?2'), [1,2])
        assert not Visitor.from_parse_results(self.parse('1?2'), [1,1,2])
        
        assert Visitor.from_parse_results(self.parse('1*2', flags=ParserState._STATEFUL), [2])
        assert Visitor.from_parse_results(self.parse('1*2', flags=ParserState._STATEFUL), [1,2])
        assert Visitor.from_parse_results(self.parse('1*2', flags=ParserState._STATEFUL), [1,1,2])
        assert not Visitor.from_parse_results(self.parse('1+2', flags=ParserState._STATEFUL), [2])
        assert Visitor.from_parse_results(self.parse('1+2', flags=ParserState._STATEFUL), [1,2])
        assert Visitor.from_parse_results(self.parse('1+2', flags=ParserState._STATEFUL), [1,1,2])
        assert Visitor.from_parse_results(self.parse('1?2', flags=ParserState._STATEFUL), [2])
        assert Visitor.from_parse_results(self.parse('1?2', flags=ParserState._STATEFUL), [1,2])
        assert not Visitor.from_parse_results(self.parse('1?2', flags=ParserState._STATEFUL), [1,1,2])

    def test_counted(self):
        v = Visitor.from_parse_results(self.parse('1{2}', flags=ParserState._STATEFUL), [1,1,1])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,2}', flags=ParserState._STATEFUL), [1,1,1])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,}', flags=ParserState._STATEFUL), [1,1,1])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{2}?', flags=ParserState._STATEFUL), [1,1,1])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,2}?', flags=ParserState._STATEFUL), [1,1,1])
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,}?', flags=ParserState._STATEFUL), [1,1,1])
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,2}?2', flags=ParserState._STATEFUL), [1,1,2])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,}?2', flags=ParserState._STATEFUL), [1,1,2])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        
        assert Visitor.from_parse_results(self.parse('1{0,}?2', flags=ParserState._STATEFUL), [2])
        assert Visitor.from_parse_results(self.parse('1{0,}?2', flags=ParserState._STATEFUL), [1,2])
        assert Visitor.from_parse_results(self.parse('1{0,}?2', flags=ParserState._STATEFUL), [1,1,2])
        assert not Visitor.from_parse_results(self.parse('1{1,}?2', flags=ParserState._STATEFUL), [2])
        assert Visitor.from_parse_results(self.parse('1{1,}?2', flags=ParserState._STATEFUL), [1,2])
        assert Visitor.from_parse_results(self.parse('1{1,}?2', flags=ParserState._STATEFUL), [1,1,2])
        assert Visitor.from_parse_results(self.parse('1{0,1}?2', flags=ParserState._STATEFUL), [2])
        assert Visitor.from_parse_results(self.parse('1{0,1}?2', flags=ParserState._STATEFUL), [1,2])
        assert not Visitor.from_parse_results(self.parse('1{0,1}?2', flags=ParserState._STATEFUL), [1,1,2])

        v = Visitor.from_parse_results(self.parse('1{2}'), [1,1,1])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,2}'), [1,1,1])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,}'), [1,1,1])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{2}?'), [1,1,1])
        assert len(v.groups[0][0]) == 2, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,2}?'), [1,1,1])
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,}?'), [1,1,1])
        assert len(v.groups[0][0]) == 1, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,2}?2'), [1,1,2])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        v = Visitor.from_parse_results(self.parse('1{1,}?2'), [1,1,2])
        assert len(v.groups[0][0]) == 3, v.groups[0][0]
        
        assert Visitor.from_parse_results(self.parse('1{0,}?2'), [2])
        assert Visitor.from_parse_results(self.parse('1{0,}?2'), [1,2])
        assert Visitor.from_parse_results(self.parse('1{0,}?2'), [1,1,2])
        assert not Visitor.from_parse_results(self.parse('1{1,}?2'), [2])
        assert Visitor.from_parse_results(self.parse('1{1,}?2'), [1,2])
        assert Visitor.from_parse_results(self.parse('1{1,}?2'), [1,1,2])
        assert Visitor.from_parse_results(self.parse('1{0,1}?2'), [2])
        assert Visitor.from_parse_results(self.parse('1{0,1}?2'), [1,2])
        assert not Visitor.from_parse_results(self.parse('1{0,1}?2'), [1,1,2])

    def test_ascii_escapes(self):
        try:
            Visitor.from_parse_results(self.parse('\\d*', flags=ParserState.ASCII), [])
            assert False
        except RxpyException:
            pass
        
    def test_unicode_escapes(self):
        try:
            Visitor.from_parse_results(self.parse('\\d'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\D'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\w'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\W'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\s'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\S'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\b'), [1])
            assert False
        except UnsupportedOperation:
            pass
        try:
            Visitor.from_parse_results(self.parse('\\B'), [])
            assert False
        except UnsupportedOperation:
            pass
    
    def test_or(self):
        assert Visitor.from_parse_results(self.parse('1|2'), [1])
        assert Visitor.from_parse_results(self.parse('1|2'), [2])
        assert not Visitor.from_parse_results(self.parse('1|2'), 'c')
        assert Visitor.from_parse_results(self.parse('(1|13)$'), [1,3])

    def test_search(self):
        assert Visitor.from_parse_results(self.parse('1'), [1,2], search=True)
        
