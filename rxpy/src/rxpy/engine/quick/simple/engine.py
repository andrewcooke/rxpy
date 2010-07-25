
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
plus the earliest start index and a matched flag).
'''


from rxpy.engine.base import BaseEngine
from rxpy.lib import UnsupportedOperation, _LOOP_UNROLL
from rxpy.engine.support import Match, Fail, lookahead_logic, Groups
from rxpy.graph.compiled import BaseCompiled, compile


class SimpleEngine(BaseEngine, BaseCompiled):
    
    REQUIRE = _LOOP_UNROLL
    
    def __init__(self, parser_state, graph, program=None):
        super(SimpleEngine, self).__init__(parser_state, graph)
        if program is None:
            program = compile(graph, self)
        self._program = program
        self.__stack = []
        
    def push(self):
        self.__stack.append((self._offset, self._text, self._search,
                             self._current, self._previous, self._states, 
                             self._group_start, self._group_defined, 
                             self._checkpoints, self._lookaheads))
        
    def pop(self):
        (self._offset, self._text, self._search,
         self._current, self._previous, self._states, 
         self._group_start, self._group_defined, 
         self._checkpoints, self._lookaheads) = self.__stack.pop()
        
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
        # TODO - add explicit search if expression starts with constant
        self._text = text
        self._set_offset(pos)
        self._search = search
        
        # handle switch to complex engine here when unsupported op raised
        return self._run_from(0)
        
    def _run_from(self, start_state):
        self._group_defined = False
        self._checkpoints = {}
        self._lookaheads = (self._offset, {})
        search = self._search # read only, deref optimisation
        
        self._states = [(start_state, self._offset, 0)]
        
        try:
            while self._states and self._offset <= len(self._text):
                
                known_next = set()
                next_states = []
                
                while self._states:
                    
                    # unpack state
                    (state, self._group_start, skip) = self._states.pop()
                    try:
                        
                        if not skip:
                            # advance a character (compiled actions recall on stack
                            # until a character is consumed)
                            next = self._program[state]()
                            if next not in known_next:
                                next_states.append((next, self._group_start, 0))
                                known_next.add(next)
                                
                        elif skip == -1:
                            raise Match

                        else:
                            skip -= 1
                            
                            # if we have other states, or will add them via search
                            if search or next_states or self._states:
                                next_states.append((state, self._group_start, skip))
                                # block this same "future state"
                                known_next.add((state, skip))
                                
                            # otherwise, we can jump directly
                            else:
                                self._offset += skip
                                next_states.append((state, self._group_start, 0))
                            
                    except Fail:
                        pass
                    
                    except Match:
                        if not next_states:
                            raise
                        next_states.append((next, self._group_start, -1))
                        known_next.add(next)
                        self._states = []
                    
                # move to next character
                self._set_offset(self._offset + 1)
                self._states = next_states
               
                # add current position as search if necessary
                if search and start_state not in known_next:
                    self._states.append((start_state, self._offset, 0))
                    
                self._states.reverse()
            
            while self._states:
                (state, self._group_start, matched) = self._states.pop()
                if matched:
                    raise Match
                
            # exhausted states with no match
            return Groups()
        
        except Match:
            
            if self._group_defined:
                raise UnsupportedOperation('groups')
            
            groups = Groups(self._parser_state.groups, self._text)
            groups.start_group(0, self._group_start)
            groups.end_group(0, self._offset)
            return groups
    
    def string(self, next, text, length):
        if length == 1:
            if self._current == text[0]:
                return True
            else:
                raise Fail
        else:
            if self._text[self._offset:self._offset+length]  == text:
                self._states.append((next, self._group_start, length))
            raise Fail
        
    def character(self, charset):
        if self._current in charset:
            return True
        else:
            raise Fail
    
    def start_group(self, number):
        return False
    
    def end_group(self, number):
        self._group_defined = True
        return False
    
    def match(self):
        raise Match

    def no_match(self):
        raise Fail

    def dot(self, multiline):
        if self._current and (multiline or self._current != '\n'):
            return True
        else:
            raise Fail
    
    def start_of_line(self, multiline):
        if self._offset == 0 or (multiline and self._previous == '\n'):
            return False
        else:
            raise Fail
    
    def end_of_line(self, multiline):
        if ((len(self._text) == self._offset or 
                    (multiline and self._current == '\n'))
                or (self._current == '\n' and
                        not self._text[self._offset+1:])):
            return False
        else:
            raise Fail
    
    def word_boundary(self, inverted):
        word = self._parser_state.alphabet.word
        boundary = word(self._current) != word(self._previous)
        if boundary != inverted:
            return False
        else:
            raise Fail

    def digit(self, inverted):
        # current here tests whether we have finished
        if self._current and \
                self._parser_state.alphabet.digit(self._current) != inverted:
            return True
        else:
            raise Fail
    
    def space(self, inverted):
        if self._current and \
                self._parser_state.alphabet.space(self._current) != inverted:
            return True
        else:
            raise Fail
        
    def word(self, inverted):
        if self._current and \
                self._parser_state.alphabet.word(self._current) != inverted:
            return True
        else:
            raise Fail
        
    def checkpoint(self, id):
        if id not in self._checkpoints or self._offset != self._checkpoints[id]:
            self._checkpoints[id] = self._offset
            return False
        else:
            raise Fail
        
    # branch

    def group_reference(self, next, number):
        raise UnsupportedOperation('group_reference')

    def conditional(self, next, number):
        raise UnsupportedOperation('conditional')

    def split(self, next):
        for (index, _node) in reversed(next):
            self._states.append((index, self._group_start, False))
        # start from new states
        raise Fail

    def lookahead(self, next, equal, forwards):
        (index, node) = next[1]
        
        # discard old values
        if self._lookaheads[0] != self._offset:
            self._lookaheads = (self._offset, {})
        lookaheads = self._lookaheads[1]
        
        if index not in lookaheads:
            
            # requires complex engine
            (reads, _mutates, size) = lookahead_logic(node, forwards, None)
            if reads:
                raise UnsupportedOperation('lookahead')
            
            # invoke simple engine and cache
            self.push()
            try:
                self._search = False
                if not forwards:
                    self._text = self._text[0:self._offset]
                    if size is None:
                        self._set_offset(0)
                        self._search = True
                    else:
                        self._set_offset(self._offset - size)
                result = bool(self._run_from(index)) == equal
            finally:
                self.pop()
            lookaheads[index] = result
            
        if lookaheads[index]:
            return 0
        else:
            raise Fail

    def repeat(self, next, begin, end, lazy):
        raise UnsupportedOperation('repeat')
