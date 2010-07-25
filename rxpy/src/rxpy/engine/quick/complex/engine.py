
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
This is an "optimized" (but largely unmeasured) engine that provides all
functionality while staying as close to Thompson's approach as possible
(DFA incrementally constructed, like re2).

It can be used standalone, but is intended to be used as a fallback from
the simple engine, when that fails on an unsupported operation. 
'''


from rxpy.engine.base import BaseEngine
from rxpy.lib import _LOOP_UNROLL
from rxpy.engine.quick.complex.support import State
from rxpy.engine.support import Match, Fail, lookahead_logic, Groups
from rxpy.graph.compiled import BaseCompiled, compile


class ComplexEngine(BaseEngine, BaseCompiled):
    
    REQUIRE = _LOOP_UNROLL
    
    def __init__(self, parser_state, graph, program=None):
        super(ComplexEngine, self).__init__(parser_state, graph)
        if program is None:
            program = compile(graph, self)
        self._program = program
        self.__stack = []
        
    def push(self):
        self.__stack.append((self._offset, self._text, self._search,
                             self._current, self._previous, self._states, 
                             self._state, self._lookaheads))
        
    def pop(self):
        (self._offset, self._text, self._search,
         self._current, self._previous, self._states, 
         self._state, self._lookaheads) = self.__stack.pop()
        
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
        self._search = search
        return self._run_from(State(0, text).start_group(0, self._offset))
        
    def _run_from(self, start_state):
        self._lookaheads = (self._offset, {})
        self._states = [start_state.clone()]
        search = self._search
        
        try:
            while self._states and self._offset <= len(self._text):
                
                known_next = set()
                next_states = []
                
                while self._states:
                    
                    self._state = self._states.pop()
                    state = self._state
                    skip = state.skip
                    
                    if not skip:
                        # advance a character (compiled actions re-call on stack
                        # until a character is consumed)
                        try:
                            state.advance(self._program[state.index]())
                            if state not in known_next:
                                next_states.append(state)
                                known_next.add(state)
                        except Fail:
                            pass
                        except Match:
                            state.skip = -1
                            if not next_states:
                                raise
                            next_states.append(state)
                            known_next.add(state)
                            
                    elif skip == -1:
                        if not next_states:
                            raise Match
                        next_states.append(state)
                        
                    else:
                        skip -= 1
                        
                        # if we have other states, or will add them via search
                        if search or next_states or self._states:
                            state.skip = skip
                            next_states.append(state)
                            known_next.add(state)
                            
                        # otherwise, we can jump directly
                        else:
                            self._offset += skip
                            state.skip = 0
                            next_states.append(state)
                    
                # move to next character
                self._set_offset(self._offset + 1)
                self._states = next_states
               
                # add current position as search if necessary
                if search and start_state not in known_next:
                    new_state = start_state.clone().start_group(0, self._offset)
                    self._states.append(new_state)
                    
                self._states.reverse()
            
            while self._states:
                self._state = self._states.pop()
                if self._state.skip == -1:
                    raise Match
                
            # exhausted states with no match
            return Groups()
        
        except Match:
            return self._state.groups(self._parser_state.groups)
    
    def string(self, next, text, length):
        if length == 1:
            if self._current == text[0]:
                return True
            else:
                raise Fail
        else:
            if self._text[self._offset:self._offset+length] == text:
                self._state.skip = length
                self._states.append(self._state.advance(next))
            raise Fail
        
    def character(self, charset):
        if self._current in charset:
            return True
        else:
            raise Fail
    
    def start_group(self, number):
        self._state.start_group(number, self._offset)
        return False
    
    def end_group(self, number):
        self._state.end_group(number, self._offset)
        return False
    
    def match(self):
        self._state.end_group(0, self._offset)
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
        self._state.check(self._offset, id)
        
    def group_reference(self, next, number):
        try:
            text = self._state.group(number)
            if text is None:
                raise Fail
            else:
                return self.string(next, text, len(text))
        except KeyError:
            raise Fail

    # branch

    def conditional(self, next, number):
        try:
            if self._state.group(number) is not None:
                return 1
        except KeyError:
            pass
        return 0

    def split(self, next):
        for (index, _node) in reversed(next):
            self._states.append(self._state.clone(index))
        # start from new states
        raise Fail

    def lookahead(self, next, equal, forwards):
        # todo - could also cache things thread groups by state
        
        (index, node) = next[1]
        
        # discard old values
        if self._lookaheads[0] != self._offset:
            self._lookaheads = (self._offset, {})
        lookaheads = self._lookaheads[1]
        
        if index in lookaheads:
            # only non-mutating non-reading values are cached 
            mutates = False
            success = lookaheads[index]
        else:
            # we need to match the lookahead
            search = False
            groups = self._state.groups(self._parser_state.groups)
            (reads, mutates, size) = lookahead_logic(node, forwards, groups)
            if forwards:
                prefix = self._text
                offset = self._offset
            else:
                prefix = self._text[0:self._offset]
                if size is None:
                    offset = 0
                    search = True
                else:
                    offset = self._offset - size
                    
            new_state = self._state.clone(index, prefix=prefix)
            
            if offset < 0:
                match = Groups()
            else:
                self.push()
                try:
                    self._text = prefix
                    self._set_offset(offset)
                    self._search = search
                    match = self._run_from(new_state)
                    new_state = self._state
                finally:
                    self.pop()
                
            success = bool(match) == equal
            if not (mutates or reads):
                lookaheads[index] = success

        # if lookahead succeeded, continue
        if success:
            if mutates and match:
                self._states.append(new_state.advance(next[0][0], text=self._text))
            else:
                self._states.append(self._state.advance(next[0][0]))
        raise Fail

    def repeat(self, next, begin, end, lazy):
        # index on first loop item
        index = next[1][0]
        state = self._state
        count = state.get_loop(index)
        if count is None:
            if 0 < begin:
                # increment and loop
                state.new_loop(index)
                return 1
            elif 0 < end:
                # can both increment and exit
                if lazy:
                    # increment on stack
                    self._states.append(state.clone(next[1][0]).new_loop(index))
                    # exit now
                    state.drop_loop(index)
                    return 0
                else:
                    # exit on stack
                    self._states.append(state.clone(next[0][0]).drop_loop(index))
                    # new loop now
                    state.new_loop(index)
                    return 1
            else:
                # strange {0,0} loop so just exit
                return 0
        else:
            count += 1
            if count < begin:
                # increment and loop
                state.increment_loop(index)
                return 1
            elif count < end:
                # can both increment and exit
                if lazy:
                    # increment on stack
                    self._states.append(state.clone(next[1][0]).increment_loop(index))
                    # exit now
                    state.drop_loop(index)
                    return 0
                else:
                    # exit on stack
                    self._states.append(state.clone(next[0][0]).drop_loop(index))
                    # new loop now
                    state.increment_loop(index)
                    return 1
            else:
                # equal to end so exit
                state.drop_loop(index)
                return 0
    