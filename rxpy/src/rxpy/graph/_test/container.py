
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


from rxpy.graph._test.lib import GraphTest
from rxpy.graph.base import BaseLabelledNode
from rxpy.graph.container import Sequence, Alternatives, Loop
from rxpy.graph.opcode import Match


def n(label):
    return BaseLabelledNode(label=str(label))


def build(sequence):
    return (None, sequence.join(Match()))


class DummyState(object):
    
    def __init__(self, flags=0):
        self.flags = flags


class ContainerTest(GraphTest):
    
    def test_sequence(self):
        self.assert_graphs(build(Sequence(n(1), n(2), n(3))),
"""strict digraph {
 0 [label="1"]
 1 [label="2"]
 2 [label="3"]
 3 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
}""")
        
    def test_alternatives(self):
        self.assert_graphs(build(Alternatives(Sequence(n(1), n(2), n(3)),
                                              Sequence(n(4), n(5)),
                                              Sequence())),
"""strict digraph {
 0 [label="...|..."]
 1 [label="1"]
 2 [label="4"]
 3 [label="Match"]
 4 [label="5"]
 5 [label="2"]
 6 [label="3"]
 0 -> 1
 0 -> 2
 0 -> 3
 2 -> 4
 4 -> 3
 1 -> 5
 5 -> 6
 6 -> 3
}""")
        
    def test_loop(self):
        self.assert_graphs(build(Loop(Sequence(n(1), n(2)),
                                      state=DummyState(), lazy=True, 
                                      label='x')),
"""strict digraph {
 0 [label="x"]
 1 [label="Match"]
 2 [label="1"]
 3 [label="2"]
 4 [label="!"]
 0 -> 1
 0 -> 2
 2 -> 3
 3 -> 4
 4 -> 0
}""")
        self.assert_graphs(build(Loop(Sequence(n(1), n(2)),
                                      state=DummyState(), lazy=False, 
                                      label='x')),
"""strict digraph {
 0 [label="x"]
 1 [label="1"]
 2 [label="Match"]
 3 [label="2"]
 4 [label="!"]
 0 -> 1
 0 -> 2
 1 -> 3
 3 -> 4
 4 -> 0
}""")
