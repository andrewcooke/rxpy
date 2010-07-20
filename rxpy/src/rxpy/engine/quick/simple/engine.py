
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

'''
An engine with a simple compiled transition table that does not support 
groups or stateful loops (so state is simply the current offset in the table
plus the earliest start index).
'''


from rxpy.engine.base import BaseEngine
from rxpy.lib import _CHARS, UnsupportedOperation
from rxpy.engine.support import Match, Fail
from rxpy.graph.compiled import BaseCompiled, compile


class SimpleEngine(BaseEngine, BaseCompiled):
    
    # single characters only to avoid incrementing any one thread out of
    # step with the others
    REQUIRE = _CHARS
    
    def __init__(self, parser_state, graph):
        super(SimpleEngine, self).__init__(parser_state, graph)
        self._program = compile(graph, self)
        
    def _set_offset(self, offset):
        self._offset = offset
        if 0 <= self._offset < len(self._text):
            self._current = self._text[self._offset]
        else:
            self._current = None
        if 0 <= self._offset-1 < len(self._text):
            self._previous = self._text[self._offset-1]
        else:
            self._previous = None
        
    def run(self, text, pos=0, search=False):
        self._text = text
        self._set_offset(pos)
        self._extra = []
        self._next = []

        if search:
            self._states = [(0, pos)]
        else:
            self._states = [0]
        
        try:
            while self._states:
                known = set()
                while self._states:
                    if search:
                        (self._state, group_start) = self._states.pop()
                    else:
                        self._state = self._states.pop()
                    try:
                        next = self._program[self._state]()
                        if next not in known:
                            if search:
                                self._next.append((next, group_start))
                            else:
                                self._next.append(next)
                            known.add(next)
                    except Fail:
                        pass
                # move to next character
                self._offset += 1
                self._previous = self._current
                try:
                    self._current = self._text[self._offset]
                except IndexError:
                    self._current = None
                self._states, self._next = self._next, []
                # add current position as search if necessary
                if search and 0 not in known and self._offset <= len(self._text):
                    self._states.append((0, self._offset))
                self._states.reverse()
            return False
        except Match:
            return True   
    
    def string(self, text):
        if self._current == text:
            return True
        else:
            raise Fail
    
    def character(self, charset):
        if self._current in charset:
            return True
        else:
            raise Fail
    
    def start_group(self, number):
        raise UnsupportedOperation('start_group')
    
    def end_group(self, number):
        raise UnsupportedOperation('end_group')
    
    def match(self):
        raise Match

    def no_match(self):
        raise Fail

    def dot(self, multiline):
        if self._current and \
                (multiline or self._current != '\n'):
            return True
        else:
            raise Fail
    
    def start_of_line(self, multiline):
        raise UnsupportedOperation('start_of_line')
    
    def end_of_line(self, multiline):
        raise UnsupportedOperation('end_of_line')
    
    def word_boundary(self, inverted):
        raise UnsupportedOperation('word_boundary')

    def digit(self, inverted):
        raise UnsupportedOperation('digit')
    
    def space(self, inverted):
        raise UnsupportedOperation('space')
    
    def word(self, inverted):
        raise UnsupportedOperation('word')
    
    def checkpoint(self):
        raise UnsupportedOperation('checkpoint')

    # branch

    def group_reference(self, next, number):
        raise UnsupportedOperation('group_reference')

    def conditional(self, next, number):
        raise UnsupportedOperation('conditional')

    def split(self, next):
        raise UnsupportedOperation('split')

    def lookahead(self, equal, forwards):
        raise UnsupportedOperation('lookahead')

    def repeat(self, begin, end, lazy):
        raise UnsupportedOperation('repeat')
