
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

from rxpy.engine.base import BaseEngine
from rxpy.graph.visitor import BaseVisitor
from rxpy.lib import _CHARS
from rxpy.engine.parallel.support import State, States
from rxpy.engine.support import Groups, lookahead_logic
from rxpy.graph.temp import Sequence
from rxpy.graph.opcode import String


class ParallelEngine(BaseEngine, BaseVisitor):
    '''
    Run an interpreter with parallel threads (effectively constructing a DFA
    "on the fly")
    '''
    
    # single characters only to avoid incrementing any one thread out of
    # step with the others
    REQUIRE = _CHARS
    
    def __init__(self, parser_state, graph, hash_state=False):
        super(ParallelEngine, self).__init__(parser_state, graph)
        self.__hash_state = hash_state
        
    def _new_state(self, groups=None, loops=None, text=None):
        if groups:
            return State(self._graph, loops=loops, groups=groups)
        else:
            return State(self._graph, loops=loops, text=text,
                         count=self._parser_state.group_count, 
                         names=self._parser_state.group_names, 
                         indices=self._parser_state.group_indices)
        
    def _new_states(self, initial):
        return States(initial, self.__hash_state)
    
    def _new_engine(self, graph):
        return type(self)(self._parser_state, graph, self.__hash_state)
        
    def run(self, text, pos=0, search=False):
        '''
        Execute a search.
        '''
        new_state = lambda: self._new_state(text=text)
        state = new_state()
        state.start_group(0, pos)
        
        state = self.run_state(state, text, pos, search, new_state)
        
        if state:
            return state.groups
        else:
            return Groups()
        
    def run_state(self, state, text, pos, search, new_state):
        
        self.__text = text
        self.__offset = pos
        self.__lookaheads = {} # can we delete some of this as we progress?
        self.__groups = {}
        
        if 0 <= pos < len(text):
            self.__current = text[pos]
        else:
            self.__current = None
        if 0 <= pos-1 < len(text):
            self.__previous = text[pos-1]
        else:
            self.__previous = None
            
        self.ticks = 0
        self.maxwidth = 0
        
        states = self._new_states([state])
        self._outer_loop(states, search, new_state)
        return states.final_state
    
    def _outer_loop(self, states, search, new_state):
        while True:
            self._inner_loop(states)
            # equals here allows final test at end of text
            if not states.final_state and self.__offset <= len(self.__text):
                if search:
                    state = new_state()
                    states.add_next(state.start_group(0, self.__offset))
                    continue
                elif states.more:
                    continue
            break
        
    def _inner_loop(self, states):
        states.flip()
        self.maxwidth = max(self.maxwidth, len(states))
        while states:
            state = states.pop()
            if not state.match:
                # extra nodes are in reverse priority - most important at end
                (state, extra) = state.graph.visit(self, state)
                self.ticks += 1
            states.add_next(state)
            states.add_extra(extra)
        self.__offset += 1
        self.__previous = self.__current
        try:
            self.__current = self.__text[self.__offset]
        except IndexError:
            self.__current = None
        
    # below are the visitor methods - these implement the different opcodes
        
    def string(self, next, text, state):
        if self.__current == text:
            return (state.advance(), [])
        return (None, [])
    
    def character(self, next, charset, state):
        if self.__current and self.__current in charset:
            return (state.advance(), [])
        return (None, [])
    
    def start_group(self, next, number, state):
        return (None, [state.start_group(number, self.__offset).advance()])
    
    def end_group(self, next, number, state):
        return (None, [state.end_group(number, self.__offset).advance()])

    def group_reference(self, next, number, state):
        try:
            text = state.groups.group(number)
            if text is None:
                return (None, [])
            elif text:
                if text not in self.__groups:
                    self.__groups[text] = \
                        Sequence([String(c) for c in text], self._parser_state)
                graph = self.__groups[text].clone()
                graph = graph.concatenate(next[0])
                return (None, [state.clone(graph=graph)])
            else:
                return (None, [state.advance()])
        except KeyError:
            return (None, [])

    def group_conditional(self, next, number, state):
        index = 1 if state.groups.group(number) else 0
        return (None, [state.advance(index)])

    def split(self, next, state):
        states = []
        for i in range(len(next)-1,-1,-1):
            if i:
                states.append(state.clone().advance(i))
            else:
                states.append(state.advance(0))
        return (None, states)
    
    def match(self, state):
        return (state.end_group(0, self.__offset), [])

    def dot(self, next, multiline, state):
        if self.__current and \
                (multiline or self.__current != '\n'):
            return (state.advance(), [])
        return (None, [])
        
    def start_of_line(self, next, multiline, state):
        if self.__offset == 0 or (multiline and self.__previous == '\n'):
            return (None, [state.advance()])
        else:
            return (None, [])
            
    def end_of_line(self, next, multiline, state):
        if ((len(self.__text) == self.__offset or 
                    (multiline and self.__current == '\n'))
                or (self.__current == '\n' and
                        not self.__text[self.__offset+1:])):
            return (None, [state.advance()])
        return (None, [])
        
    def lookahead(self, next, node, equal, forwards, state):
        if node not in self.__lookaheads:
            self.__lookaheads[node] = {}
        if self.__offset not in self.__lookaheads[node]:
            # we need to match the lookahead
            search = False
            (reads, mutates, size) = lookahead_logic(next[1], forwards, state.groups)
            if forwards:
                subtext = self.__text
                offset = self.__offset
            else:
                subtext = self.__text[0:self.__offset]
                if size is None:
                    offset = 0
                    search = True
                else:
                    offset = self.__offset - size
            if reads or mutates:
                groups = state.groups
                new_state = lambda: engine._new_state(groups=groups)
            else:
                groups = None
                new_state = lambda: engine._new_state(text=subtext)
            engine = self._new_engine(next[1])
            match = engine.run_state(state.clone(graph=next[1], groups=groups), 
                                     subtext, pos=offset, search=search,
                                     new_state=new_state)
            self.ticks += engine.ticks
            success = bool(match) == equal
            if not (mutates or reads):
                self.__lookaheads[node][self.__offset] = success
        else:
            mutates = False
            success = self.__lookaheads[node][self.__offset]
        # if lookahead succeeded, continue
        if success:
            if mutates:
                return (None, [state.clone(groups=match.groups).advance()])
            else:
                return (None, [state.advance()])
        else:
            return (None, [])

    def repeat(self, next, node, begin, end, lazy, state):
        count = state.increment(node)
        # if we haven't yet reached the point where we can continue, loop
        if count < begin:
            return (None, [state.advance(1)])
        # otherwise, logic depends on laziness
        states = []
        if lazy:
            # continuation is highest priority, but if that fails we restart 
            # with another loop, unless we've exceeded the count or there's
            # no text left
            if (end is None and self.__current) \
                    or (end is not None and count < end):
                states.append(state.clone().advance(1))
            if end is None or count <= end:
                states.append(state.drop(node).advance())
        else:
            if end is None or count < end:
                # add a fallback so that if a higher loop fails, we can continue
                states.append(state.clone().drop(node).advance())
            if count == end:
                # if last possible loop, continue
                states.append(state.drop(node).advance())
            else:
                # otherwise, do another loop
                states.append(state.advance(1))
        return (None, states)
    
    def word_boundary(self, next, inverted, state):
        word = self._parser_state.alphabet.word
        boundary = word(self.__current) != word(self.__previous)
        if boundary != inverted:
            return (None, [state.advance()])
        else:
            return (None, [])

    def digit(self, next, inverted, state):
        # current here tests whether we have finished
        if self.__current and \
                self._parser_state.alphabet.digit(self.__current) != inverted:
            return (state.advance(), [])
        return (None, [])
    
    def space(self, next, inverted, state):
        if self.__current and \
                self._parser_state.alphabet.space(self.__current) != inverted:
            return (state.advance(), [])
        return (None, [])
    
    def word(self, next, inverted, state):
        if self.__current and \
                self._parser_state.alphabet.word(self.__current) != inverted:
            return (state.advance(), [])
        return (None, [])
