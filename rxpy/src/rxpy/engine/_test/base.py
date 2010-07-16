
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


from rxpy.compat.module import Re
from rxpy.alphabet.unicode import Unicode
from rxpy.parser.pattern import parse_pattern
from rxpy.lib import unimplemented


class BaseTest(object):

    @unimplemented
    def default_engine(self):
        '''
        Should return an engine class
        '''
        
    def default_alphabet(self):
        return None
    
    def setUp(self):
        self._alphabet = self.default_alphabet()
        self._re = Re(self.default_engine())
        
    def parse(self, regexp, flags=0, alphabet=None):
        return parse_pattern(regexp, self.default_engine(),
                             alphabet=alphabet if alphabet else self._alphabet, 
                             flags=flags)
    
    def engine(self, parse, text, search=False, 
               ticks=None, maxdepth=None):
        engine = self.default_engine()(*parse)
        result = engine.run(text, search=search)
        if ticks is not None:
            assert engine.ticks == ticks, engine.ticks
        if maxdepth is not None:
            assert engine.maxdepth == maxdepth, engine.maxdepth
        return result

