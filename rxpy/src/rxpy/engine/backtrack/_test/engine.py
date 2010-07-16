
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

from rxpy.engine.backtrack.engine import BacktrackingEngine
from rxpy.engine._test.engine import EngineTest


class BacktrackingEngineTest(EngineTest, TestCase):
    
    def default_engine(self):
        return BacktrackingEngine
    
    def test_stack(self):
        # optimized
        assert self.engine(self.parse('(?:abc)*x'), ('abc' * 50000) + 'x',  maxdepth=1)
        # this defines a group, so requires state on stack
        assert self.engine(self.parse('(abc)*x'), ('abc' * 5) + 'x',  maxdepth=6)
        # this is lazy, so doesn't
        assert self.engine(self.parse('(abc)*?x'), ('abc' * 5) + 'x',  maxdepth=1)
        
    def test_lookback_with_offset(self):
        assert self.engine(self.parse('..(?<=a)'), 'xa', ticks=7)
        assert not self.engine(self.parse('..(?<=a)'), 'ax')
        
    def test_lookback_optimisations(self):
        assert self.engine(self.parse('(.).(?<=a)'), 'xa', ticks=9)
        # only one more tick with an extra character because we avoid starting
        # from the start in this case
        assert self.engine(self.parse('.(.).(?<=a)'), 'xxa', ticks=10)
        
        assert self.engine(self.parse('(.).(?<=\\1)'), 'aa', ticks=9)
        # again, just one tick more
        assert self.engine(self.parse('.(.).(?<=\\1)'), 'xaa', ticks=10)
        assert not self.engine(self.parse('.(.).(?<=\\1)'), 'xxa')
        
        assert self.engine(self.parse('(.).(?<=(\\1))'), 'aa', ticks=15)
        # but here, three ticks more because we have a group reference with
        # changing groups, so can't reliably calculate lookback distance
        assert self.engine(self.parse('.(.).(?<=(\\1))'), 'xaa', ticks=18)
        assert not self.engine(self.parse('.(.).(?<=(\\1))'), 'xxa')
        
        assert self.engine(self.parse('(.).(?<=a)'), 'xa', ticks=9)

        assert self.engine(self.parse('(.).(?<=(?:a|z))'), 'xa', ticks=10)
        assert self.engine(self.parse('(.).(?<=(a|z))'), 'xa', ticks=12)
        # only one more tick with an extra character because we avoid starting
        # from the start in this case
        assert self.engine(self.parse('.(.).(?<=(?:a|z))'), 'xxa', ticks=11)
        assert self.engine(self.parse('.(.).(?<=(a|z))'), 'xxa', ticks=13)
        
