
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


from rxpy.graph.base import BaseNode
from rxpy.graph.opcode import Split, CheckPoint
from rxpy.lib import unimplemented
from rxpy.parser.support import ParserState


class BaseCollection(object):
    
    def __init__(self, *contents):
        for content in contents:
            self._check(content)
        self._contents = list(contents)
        
    def append(self, content):
        self._check(content)
        self._contents.append(content)

    @unimplemented
    def _check(self, content):
        pass
    
    @unimplemented
    def consumer(self, lenient):
        pass
    
    def clone(self):
        contents = list(map(lambda x: x.clone(), self._contents))
        return type(self)(*contents)
    

class Sequence(BaseCollection):
    
    def _check(self, content):
        assert isinstance(content, BaseNode) or isinstance(content, BaseCollection)
    
    def consumer(self, lenient):
        for node in self._contents:
            if node.consumer(lenient):
                return True
        return False
    
    def join(self, final):
        for content in reversed(self._contents):
            final = content.join(final)
        return final
    

class Alternatives(BaseCollection):
    
    def _check(self, content):
        assert isinstance(content, Sequence)
    
    def consumer(self, lenient):
        for sequence in self._contents:
            if not sequence.consumer(lenient):
                return False
        return True
    
    def join(self, final):
        split = Split('...|...')
        split.next = list(map(lambda x: x.join(final), self._contents))
        return split


class Loop(Alternatives):
    
    def __init__(self, content, state=None, lazy=None, label=None):
        if not content.consumer(False) and not (state.flags & ParserState._UNSAFE):
            content.append(CheckPoint())
        super(Loop, self).__init__(content)
        self.__lazy = lazy
        self.__label = label

    def clone(self):
        clone = super(Loop, self).clone()
        clone.__lazy = self.__lazy
        clone.__label = self.__label
        return clone

    def join(self, final):
        split = Split(self.__label, consumes=True)
        next = [final, self._contents[0].join(split)]
        if not self.__lazy:
            next.reverse()
        split.next = next
        return split
