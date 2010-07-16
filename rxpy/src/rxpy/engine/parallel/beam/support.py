
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


from rxpy.engine.parallel.support import States as BaseStates

class States(BaseStates):
    
    def __init__(self, initial, hash_state, beam_start=1, beam_scale=2):
        super(States, self).__init__(initial, hash_state)
        self.__initial = list(map(lambda x: x.clone(), initial))
        self.__beam_width = beam_start
        self.__beam_scale = beam_scale
        self.__overflowed = False
        
    def grow(self):
        self.__overflowed = False
        self.__beam_width *= self.__beam_scale
        self._next_nodes = list(map(lambda x: x.clone(), self.__initial))
        
    @property
    def overflowed(self):
        return self.__overflowed

    def add_next(self, next):
        if len(self._next_nodes) == self.__beam_width:
            self.__overflowed = True
            # since we are rejecting a success, we must discard all 
            # alternatives "below" that.  we can then continue to accept
            # future alternatives next iteration.
            self._current_nodes = []
        else:
            super(States, self).add_next(next)
