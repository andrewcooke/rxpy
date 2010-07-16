
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


from rxpy.engine.parallel.base import ParallelEngine
from rxpy.engine.parallel.beam.support import States


class BeamEngine(ParallelEngine):
    
    def __init__(self, parser_state, graph, hash_state=False,
                 beam_start=1, beam_scale=2):
        super(BeamEngine, self).__init__(parser_state, graph, 
                                         hash_state=hash_state)
        self.__beam_start = beam_start
        self.__beam_scale = beam_scale

    def _new_states(self, initial):
        return States(initial, self._hash_state, 
                      beam_start=self.__beam_start, beam_scale=self.__beam_scale)
    
    def _outer_loop(self, states, search, new_state):
        initial_offset = self._offset
        growing = True
        while not states.final_state and growing:
            super(BeamEngine, self)._outer_loop(states, search, new_state)
            if not states.final_state and states.overflowed:
                growing = True
                states.grow()
                self._set_offset(initial_offset)
            else:
                growing = False

