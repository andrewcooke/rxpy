
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

from rxpy.alphabet.base import CharSet
from rxpy.alphabet.digits import Digits


class CharSetTest(TestCase):
    
    def do_test_str(self, intervals, target):
        result = str(CharSet(intervals, alphabet=Digits()))
        assert result == target, result
    
    def test_str(self):
        self.do_test_str([], '[]')
        self.do_test_str([('0','0')], '[0]')
        self.do_test_str([('0','1')], '[01]')
        self.do_test_str([('0','2')], '[0-2]')
        self.do_test_str([('0','0'), ('1', '1')], '[01]')
       
    def test_coallesce(self):
        self.do_test_str([('0','0'), ('2', '2')], '[02]')
        self.do_test_str([('0','0'), ('1', '2')], '[0-2]')
        self.do_test_str([('0','1'), ('0', '2')], '[0-2]')
        self.do_test_str([('0','1'), ('1', '2')], '[0-2]')
        self.do_test_str([('0','2'), ('2', '2')], '[0-2]')
        self.do_test_str([('1','2'), ('0', '1')], '[0-2]')
        self.do_test_str([('2','2'), ('0', '0')], '[02]')
        self.do_test_str([('0','2'), ('6', '9')], '[0-26-9]')
        self.do_test_str([('1','2'), ('6', '9')], '[126-9]')
        self.do_test_str([('1','2'), ('0', '9')], '[0-9]')
    
    def test_reversed(self):
        self.do_test_str([('2','0')], '[0-2]')
        self.do_test_str([('1','0')], '[01]')
        self.do_test_str([('1','0'), ('1', '2')], '[0-2]')
    
    def test_contains(self):
        assert 0 not in CharSet([('1', '1')], Digits())
        assert 1 in CharSet([('1', '1')], Digits())
        assert 2 not in CharSet([('1', '1')], Digits())
        assert 0 in CharSet([('0', '1')], Digits())
        assert 1 in CharSet([('0', '1')], Digits())
        assert 2 not in CharSet([('0', '1')], Digits())
        assert 0 in CharSet([('0', '2')], Digits())
        assert 1 in CharSet([('0', '2')], Digits())
        assert 2 in CharSet([('0', '2')], Digits())
        assert 0 in CharSet([('0', '1'), ('1', '2')], Digits())
        assert 1 in CharSet([('0', '1'), ('1', '2')], Digits())
        assert 2 in CharSet([('0', '1'), ('1', '2')], Digits())
        assert 0 in CharSet([('0', '0'), ('2', '2')], Digits())
        assert 1 not in CharSet([('0', '0'), ('2', '2')], Digits())
        assert 2 in CharSet([('0', '0'), ('2', '2')], Digits())
