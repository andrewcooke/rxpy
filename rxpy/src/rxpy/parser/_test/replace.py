
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


from rxpy.lib import _CHARS
from rxpy.graph._test.lib import GraphTest
from rxpy.engine.base import BaseEngine
from rxpy.parser.replace import parse_replace
from rxpy.parser.pattern import parse_pattern


class DummyEngine(BaseEngine):
    REQUIRE = _CHARS
    

def parse(pattern, replacement):
    (state, _graph) = parse_pattern(pattern, BaseEngine)
    return parse_replace(replacement, state)


class ParserTest(GraphTest):
    
    def test_string(self):
        self.assert_graphs(parse('', 'abc'), 
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_single_group(self):
        self.assert_graphs(parse('(.)', '\\1'), 
"""digraph {
 0 [label="\\\\1"]
 1 [label="Match"]
 0 -> 1
}""")

        
