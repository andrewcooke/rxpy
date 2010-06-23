

from unittest import TestCase

from rxpy.alphabet.base import CharSet
from rxpy.alphabet.ascii import Ascii

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


class CharSetTest(TestCase):
    
    def do_test_str(self, intervals, target):
        result = str(CharSet(intervals, Ascii()))
        assert result == target, result
    
    def test_str(self):
        self.do_test_str([], '[]')
        self.do_test_str([('a','a')], '[a]')
        self.do_test_str([('a','b')], '[ab]')
        self.do_test_str([('a','c')], '[a-c]')
        self.do_test_str([('a','a'), ('b', 'b')], '[ab]')
       
    def test_coallesce(self):
        self.do_test_str([('a','a'), ('c', 'c')], '[ac]')
        self.do_test_str([('a','a'), ('b', 'c')], '[a-c]')
        self.do_test_str([('a','b'), ('a', 'c')], '[a-c]')
        self.do_test_str([('a','b'), ('b', 'c')], '[a-c]')
        self.do_test_str([('a','c'), ('c', 'c')], '[a-c]')
        self.do_test_str([('b','c'), ('a', 'b')], '[a-c]')
        self.do_test_str([('c','c'), ('a', 'a')], '[ac]')
        self.do_test_str([('a','c'), ('p', 's')], '[a-cp-s]')
        self.do_test_str([('b','c'), ('p', 's')], '[bcp-s]')
        self.do_test_str([('b','c'), ('a', 's')], '[a-s]')
    
    def test_reversed(self):
        self.do_test_str([('c','a')], '[a-c]')
        self.do_test_str([('b','a')], '[ab]')
        self.do_test_str([('b','a'), ('b', 'c')], '[a-c]')
    
    def test_contains(self):
        assert 'a' not in CharSet([('b', 'b')], Ascii())
        assert 'b' in CharSet([('b', 'b')], Ascii())
        assert 'c' not in CharSet([('b', 'b')], Ascii())
        assert 'a' in CharSet([('a', 'b')], Ascii())
        assert 'b' in CharSet([('a', 'b')], Ascii())
        assert 'c' not in CharSet([('a', 'b')], Ascii())
        assert 'a' in CharSet([('a', 'c')], Ascii())
        assert 'b' in CharSet([('a', 'c')], Ascii())
        assert 'c' in CharSet([('a', 'c')], Ascii())
        assert 'a' in CharSet([('a', 'b'), ('b', 'c')], Ascii())
        assert 'b' in CharSet([('a', 'b'), ('b', 'c')], Ascii())
        assert 'c' in CharSet([('a', 'b'), ('b', 'c')], Ascii())
        assert 'a' in CharSet([('a', 'a'), ('c', 'c')], Ascii())
        assert 'b' not in CharSet([('a', 'a'), ('c', 'c')], Ascii())
        assert 'c' in CharSet([('a', 'a'), ('c', 'c')], Ascii())
