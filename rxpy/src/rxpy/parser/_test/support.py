
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
from rxpy.parser.support import GroupState
from rxpy.lib import RxpyException


class GroupStateTest(TestCase):
    
    def test_basic(self):
        state = GroupState()
        assert 1 == state.new_index()
        assert 2 == state.new_index()
        assert 2 == state.count
        
    def test_alias(self):
        state = GroupState()
        assert 1 == state.new_index()
        assert 1 == state.new_index(name='1', extended=True)
        assert 1 == state.count
        try:
            state.new_index(name='1', extended=False)
            assert False, 'expected error'
        except RxpyException:
            pass
    
    def test_non_contiguous(self):
        state = GroupState()
        assert 1 == state.new_index()
        assert 7 == state.new_index(name='7', extended=True)
        assert 2 == state.count
        try:
            state.new_index(name='8', extended=False)
            assert False, 'expected error'
        except RxpyException:
            pass
        assert 2 == state.new_index()
        assert 3 == state.count
    
    def test_names(self):
        state = GroupState()
        assert 1 == state.new_index()
        assert 2 == state.new_index(name='bob')
        assert 2 == state.count
        try:
            assert 2 == state.new_index(name='bob')
            assert False, 'expected error'
        except RxpyException:
            pass
        assert 2 == state.count
        assert 2 == state.new_index(name='bob', extended=True)
        assert 2 == state.count
        

