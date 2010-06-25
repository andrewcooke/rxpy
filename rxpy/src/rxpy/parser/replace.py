
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


from string import digits

from rxpy.lib import RxpyException
from rxpy.graph.temp import Sequence
from rxpy.parser.parser import IntermediateEscapeBuilder
from rxpy.parser.support import parse, StatefulBuilder, ALPHANUMERIC
from rxpy.graph.opcode import GroupReference, Match, String


def parse_repl(text, state):
    return parse(text, state, class_=ReplacementBuilder, mutable_flags=False)

class ReplacementEscapeBuilder(IntermediateEscapeBuilder):
    
    def append_character(self, character):
        if not character:
            raise RxpyException('Incomplete character escape')
        elif character == 'g':
            return ReplacementGroupReferenceBuilder(self._state, 
                                                    self._parent_builder)
        else:
            return super(ReplacementEscapeBuilder, self).append_character(character)
        
    def _unexpected_character(self, character):
        '''
        Unexpected escapes are preserved during substitution.
        '''
        self._parent_builder.append_character('\\', escaped=True)
        self._parent_builder.append_character(character, escaped=True)
        return self._parent_builder
        
        
class ReplacementGroupReferenceBuilder(StatefulBuilder):
    
    def __init__(self, state, parent):
        super(ReplacementGroupReferenceBuilder, self).__init__(state)
        self.__parent_sequence = parent
        self.__buffer = ''
        
    def __decode(self):
        try:
            return GroupReference(
                    self._state.index_for_name_or_count(self.__buffer[1:]))
        except RxpyException:
            raise IndexError('Bad group reference: ' + self.__buffer[1:])
        
    @property
    def __numeric(self):
        if not self.__buffer:
            return False
        elif not self.__buffer[1:]:
            return True
        else:
            try:
                int(self.__buffer[1:])
                return True
            except:
                return False
            
    @property
    def __name(self):
        if not self.__buffer:
            return False
        elif not self.__buffer[1:]:
            return True
        return not self.__buffer[1] in digits
             
        
    def append_character(self, character):
        # this is so complex because the tests for different errors are so
        # detailed
        if not self.__buffer and character == '<':
            self.__buffer += character
            return self
        elif len(self.__buffer) > 1 and character == '>':
            self.__parent_sequence._nodes.append(self.__decode())
            return self.__parent_sequence
        elif character and self.__numeric and character in digits:
            self.__buffer += character
            return self
        elif character and self.__name and character in ALPHANUMERIC:
            self.__buffer += character
            return self
        elif character:
            raise RxpyException('Unexpected character in group escape: ' + character)
        else:
            raise RxpyException('Incomplete group escape')
        

class ReplacementBuilder(StatefulBuilder):
    '''
    A separate builder (which uses escape handling above) used to parse the
    "replacement" string for the "subn" method.
    '''
    
    def __init__(self, state):
        # we want to preserve the type of the output in python2.6; that means
        # switching between ASCII and Unicode depending on the input.
        super(ReplacementBuilder, self).__init__(state)
        self._nodes = []
        
    def parse(self, text):
        builder = self
        for character in text:
            builder = builder.append_character(character)
        builder = builder.append_character(None)
        if self != builder:
            raise RxpyException('Incomplete expression')
        return self.build_dag().concatenate(Match())
    
    def append_character(self, character, escaped=False):
        if not escaped and character == '\\':
            return ReplacementEscapeBuilder(self._state, self)
        elif character:
            # ignore case here - used only for replacement
            self._nodes.append(
                String(self._state.alphabet.join(
                            self._state.alphabet.coerce(character))))
        return self
    
    def build_dag(self):
        return Sequence(self._nodes, self._state)

