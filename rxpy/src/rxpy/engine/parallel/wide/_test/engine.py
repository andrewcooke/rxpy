
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

from rxpy.engine._test.engine import EngineTest
from rxpy.engine.parallel.wide.engine import WideEngine


class WideEngineTest(EngineTest, TestCase):
    
    def default_engine(self):
        return WideEngine

    def test_lookback_with_offset(self):
        assert self.engine(self.parse('..(?<=a)'), 'xa', ticks=7)
        assert not self.engine(self.parse('..(?<=a)'), 'ax')
        
    def test_lookback_optimisations(self):
        assert self.engine(self.parse('(.).(?<=a)'), 'xa', ticks=9)
        # only one more tick with an extra character because we avoid starting
        # from the start in this case
        assert self.engine(self.parse('.(.).(?<=a)'), 'xxa', ticks=10)
        
        assert self.engine(self.parse('(.).(?<=\\1)'), 'aa', ticks=10)
        # again, just one tick more
        assert self.engine(self.parse('.(.).(?<=\\1)'), 'xaa', ticks=11)
        assert not self.engine(self.parse('.(.).(?<=\\1)'), 'xxa')
        
        assert self.engine(self.parse('(.).(?<=(\\1))'), 'aa')
        assert self.engine(self.parse('(.).(?<=(\\1))'), 'aa', ticks=18)
        # but here, three ticks more because we have a group reference with
        # changing groups, so can't reliably calculate lookback distance
        assert self.engine(self.parse('.(.).(?<=(\\1))'), 'xaa', ticks=22)
        assert not self.engine(self.parse('.(.).(?<=(\\1))'), 'xxa')
        
        assert self.engine(self.parse('(.).(?<=a)'), 'xa', ticks=9)

        assert self.engine(self.parse('(.).(?<=(?:a|z))'), 'xa', ticks=11)
        assert self.engine(self.parse('(.).(?<=(a|z))'), 'xa', ticks=13)
        # only one more tick with an extra character because we avoid starting
        # from the start in this case
        assert self.engine(self.parse('.(.).(?<=(?:a|z))'), 'xxa', ticks=12)
        assert self.engine(self.parse('.(.).(?<=(a|z))'), 'xxa', ticks=14)
        
        
    def test_width_basics(self):
        # width of 2 as carrying fallback match
        assert self.engine(self.parse('b*'), 1000 * 'b', ticks=3003, maxwidth=2)
        assert self.engine(self.parse('b*'), 1000 * 'b' + 'c', ticks=3003, maxwidth=2)
        # width of 1 when no match until end
        assert self.engine(self.parse('b*c'), 1000 * 'b' + 'c', ticks=3004, maxwidth=1)
        assert self.engine(self.parse('b*?c'), 1000 * 'b' + 'c', ticks=3004, maxwidth=1)
        assert self.engine(self.parse('ab*c'), 'a' + 1000 * 'b' + 'c', ticks=3005, maxwidth=1)
        assert self.engine(self.parse('ab*?c'), 'a' + 1000 * 'b' + 'c', ticks=3005, maxwidth=1)

    def test_width_hash_state(self):
        # equivalently, we can use hashing (which shortcuts on match)
        assert self.engine(self.parse('b*'), 1000 * 'b', ticks=3003, maxwidth=2, hash_state=True)
    
    def test_width_groups(self):
        assert self.engine(self.parse('(b)*'), 1000 * 'b', ticks=5004, maxwidth=2)
        assert self.engine(self.parse('(b)*'), 1000 * 'b' + 'c', ticks=5004, maxwidth=2)
        assert self.engine(self.parse('(b)*c'), 1000 * 'b' + 'c', ticks=5005, maxwidth=1)
        assert self.engine(self.parse('(b)*?c'), 1000 * 'b' + 'c', ticks=5005, maxwidth=1)
        assert self.engine(self.parse('a(b)*c'), 'a' + 1000 * 'b' + 'c', ticks=5006, maxwidth=1)
        assert self.engine(self.parse('a(b)*?c'), 'a' + 1000 * 'b' + 'c', ticks=5006, maxwidth=1)
        assert self.engine(self.parse('(b)*'), 1000 * 'b', ticks=5004, maxwidth=2, hash_state=True)

    def test_width_re_test(self):
        assert self.engine(self.parse('.*?cd'), 1000*'abc'+'de', ticks=10005, maxwidth=2)
        # this could be optimised as a character
        assert self.engine(self.parse('(a|b)*?c'), 1000*'ab'+'cd', ticks=14007, maxwidth=1)

    def test_width_search(self):
#        bk = 1000 * 'b'
        bk = 100 * 'b'
        result = self.engine(self.parse('b*'), bk, search=True)
        assert result
        assert result.group(0) == bk, result.group(0)
        
        assert self.engine(self.parse('b*'), bk, ticks=303, maxwidth=2, search=True)
        assert self.engine(self.parse('b*'), bk, ticks=303, maxwidth=2, hash_state=True, search=True)
        assert self.engine(self.parse('.*?b*'), bk, ticks=305, maxwidth=2)
        assert self.engine(self.parse('.*?b*'), bk, ticks=305, maxwidth=2, hash_state=True)

        assert self.engine(self.parse('b*'), bk + 'c', ticks=303, maxwidth=2, search=True)
        assert self.engine(self.parse('b*'), bk + 'c', ticks=303, maxwidth=2, hash_state=True, search=True)
        assert self.engine(self.parse('b*c'), bk + 'c', ticks=15555, maxwidth=102, search=True)
        assert self.engine(self.parse('b*c'), bk + 'c', ticks=305, maxwidth=2, hash_state=True, search=True)
        assert self.engine(self.parse('b*?c'), bk + 'c', ticks=15555, maxwidth=102, search=True)
        assert self.engine(self.parse('b*?c'), bk + 'c', ticks=305, maxwidth=2, hash_state=True, search=True)
        assert self.engine(self.parse('ab*c'), 'a' + bk + 'c', ticks=407, maxwidth=2, search=True)
        assert self.engine(self.parse('ab*c'), 'a' + bk + 'c', ticks=407, maxwidth=2, hash_state=True, search=True)
        assert self.engine(self.parse('ab*?c'), 'a' + bk + 'c', ticks=407, maxwidth=2, search=True)
        assert self.engine(self.parse('ab*?c'), 'a' + bk + 'c', ticks=407, maxwidth=2, hash_state=True, search=True)

        assert self.engine(self.parse('b*c'), bk + 'c', ticks=15555, maxwidth=102, search=True)
        assert self.engine(self.parse('b*c'), bk + 'c', ticks=305, maxwidth=2, hash_state=True, search=True)
        assert self.engine(self.parse('.*?b*c'), bk + 'c', ticks=15757, maxwidth=102)
        assert self.engine(self.parse('.*?b*c'), bk + 'c', ticks=807, maxwidth=2, hash_state=True)
