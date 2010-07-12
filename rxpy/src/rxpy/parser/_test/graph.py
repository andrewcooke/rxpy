
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


from rxpy.parser._test.lib import GraphTest
from rxpy.parser.pattern import parse_pattern
from rxpy.parser.support import ParserState
from rxpy.engine.base import BaseEngine


def parse(pattern, flags=0):
    return parse_pattern(pattern, BaseEngine, flags=flags)

class ReprTest(GraphTest):
    
    def test_already_connected_bug(self):
        parse('a')
        parse('b')
        parse('(c|e)')
        parse('d')
        parse('(c|e)')
        parse('c{1,2}', )
        parse('c{1,2}')
        parse('(c|e){1,2}', flags=ParserState._LOOP_UNROLL)
        parse('(c|e){1,2}')
        parse('(c|e){1,2}?')
        parse('(b|(c|e){1,2}?|d)')
        parse('(?:b|(c|e){1,2}?|d)')
        parse('(?:b|(c|e){1,2}?|d)+?')
        parse('(.)')
        parse('a(?:b|(c|e){1,2}?|d)+?(.)')

    def test_w3_bug(self):
        self.assert_graphs(parse('\w{3}(?_l)$'),
"""digraph {
 0 [label="\\\\w"]
 1 [label="\\\\w"]
 2 [label="\\\\w"]
 3 [label="$"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")
        self.assert_graphs(parse('(\w)$'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="\\\\w"]
 2 [label=")"]
 3 [label="$"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")
        self.assert_graphs(parse('(\w){3}$(?_l)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="\\\\w"]
 2 [label=")"]
 3 [label="(?P<1>"]
 4 [label="\\\\w"]
 5 [label=")"]
 6 [label="(?P<1>"]
 7 [label="\\\\w"]
 8 [label=")"]
 9 [label="$"]
 10 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 7
 7 -> 8
 8 -> 9
 9 -> 10
}""")
        