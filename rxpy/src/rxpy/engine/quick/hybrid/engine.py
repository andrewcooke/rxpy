
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



from rxpy.engine.quick.simple.engine import SimpleEngine
from rxpy.lib import UnsupportedOperation
from rxpy.engine.quick.complex.engine import ComplexEngine


class HybridEngine(SimpleEngine):
    
    def __init__(self, parser_state, graph, program=None):
        super(HybridEngine, self).__init__(parser_state, graph, program=program)
        self.__cached_fallback = None
    
    def run(self, text, pos=0, search=False):
        self._group_defined = False

        try:
            results = self._run_from(0, text, pos, search)
            
            if self._group_defined:
                # reprocess using only the exact region matched
                return self.__fallback.run(text, results.start(0))
            else:
                return results
            
        except UnsupportedOperation:
            # todo - restart from exact position (will need to set index in
            # compiled function stack by catching exception)
            return self.__fallback.run(text, pos=pos, search=search)
        
    @property
    def __fallback(self):
        if self.__cached_fallback is None:
            self.__cached_fallback = ComplexEngine(self._parser_state, self._graph)
        return self.__cached_fallback

        
