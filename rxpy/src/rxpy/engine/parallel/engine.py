from rxpy.graph.support import contains_instance, ReadsGroup
from rxpy.graph.opcode import StartGroup, String
from rxpy.graph.temp import Sequence

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
A matcher implementation that explores threads in parallel, providing better
scaling for complex matches.
'''

from rxpy.engine.base import BaseEngine
from rxpy.engine.support import Loops, Groups
from rxpy.graph.visitor import BaseVisitor
from rxpy.lib import _STRINGS, UnsupportedOperation


class State(object):
    '''
    State for a particular thread (offset in the text is common to all threads).
    '''
    
    def __init__(self, graph, groups=None, loops=None, **groups_kargs):
        self.__graph = graph
        self.__groups = groups if groups is not None else [None, None, groups_kargs]
        self.__loops = loops
        self.match = False
        
    def clone(self, graph=None):
        try:
            groups = self.__groups.clone()
        except AttributeError:
            groups = list(self.__groups)
        try:
            loops = self.__loops.clone()
        except AttributeError:
            loops = self.__loops
        return State(self.__graph if graph is None else graph, 
                     groups=groups, loops=loops)
    
    def start_group(self, number, offset):
        if number == 0:
            try:
                self.__groups[0] = offset
                return self
            except TypeError:
                pass
        self.__expand_groups()
        self.__groups.start_group(number, offset)
        return self
        
    def end_group(self, number, offset):
        if number == 0:
            try:
                self.__groups[1] = offset
                return self
            except TypeError:
                pass
        self.__expand_groups()
        self.__groups.end_group(number, offset)
        return self
    
    def __expand_groups(self):
        if not isinstance(self.__groups, Groups):
            save = self.__groups
            self.__groups = Groups(**save[2])
            if save[0] is not None:
                self.__groups.start_group(0, save[0])
            if save[1] is not None:
                self.__groups.end_group(0, save[1])
    
    def increment(self, node):
        self.__expand_loops()
        return self.__loops.increment(node)
    
    def drop(self, node):
        self.__expand_loops()
        self.__loops.drop(node)
        return self
    
    def __expand_loops(self):
        if not self.__loops:
            self.__loops = Loops()
    
    def advance(self, index=0):
        self.__graph = self.__graph.next[index]
        return self
    
    @property
    def graph(self):
        return self.__graph
    
    @property
    def groups(self):
        self.__expand_groups()
        return self.__groups
    
    
class ParallelEngine(BaseEngine, BaseVisitor):
    '''
    Run an interpreter with parallel threads (effectively constructing a DFA
    "on the fly")
    '''
    
    # single characters only to avoid incrementing any one thread out of
    # step with the others
    REJECT = _STRINGS
    
    def run(self, text, pos=0, search=False):
        '''
        Execute a search.
        '''
        state = State(self._graph,
                      text=text, count=self._parser_state.group_count, 
                      names=self._parser_state.group_names, 
                      indices=self._parser_state.group_indices)
        state.start_group(0, pos)
        
        state = self.run_state(state, text, pos, search)
        
        if state:
            return state.groups
        else:
            return Groups()
        
    def run_state(self, state, text, pos=0, search=False, groups=None):
        
        self.__text = text
        self.__offset = pos
        self.__lookaheads = {} # can we delete some of this as we progress?
        self.__groups = {}
        
        self.ticks = 0
        self.maxwidth = 0
        
        current_states, next_states = [state], []

        while current_states and not current_states[-1].match:
            self.maxwidth = max(self.maxwidth, len(current_states))
            try:
                self.__previous = self.__text[self.__offset-1]
            except IndexError:
                self.__previous = None
            try:
                self.__current = self.__text[self.__offset]
            except IndexError:
                self.__current = None
            while current_states:
                state = current_states.pop()
                # extra nodes are in reverse priority - most important at end
                (updated, extra) = state.graph.visit(self, state)
                self.ticks += 1
                if updated:
                    next_states.append(updated)
                # we process extra states immediately
                current_states.extend(extra)
            self.__offset += 1
            current_states, next_states = next_states, []
            if search and self.__offset < len(self.__text):
                if groups:
                    state = State(self._graph, groups=groups)
                else:
                    state = State(self._graph,
                                  text=text, count=self._parser_state.group_count, 
                                  names=self._parser_state.group_names, 
                                  indices=self._parser_state.group_indices)
                current_states.append(state.start_group(0, self.__offset))
            current_states.reverse()
        
        if current_states:
            return current_states[-1]
        else:
            return None
        
    # below are the visitor methods - these implement the different opcodes
    # (typically by modifying state and returning the next node) 
        
    def string(self, next, text, state):
        if self.__current == text:
            return (state.advance(), [])
        return (None, [])
    
    def character(self, next, charset, state):
        if self.__current in charset:
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
                return (None, [state.clone(graph)])
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
        if not state.match:
            state.match = True
            state.end_group(0, self.__offset)
        return (state, [])

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
            groups = None
            if forwards:
                offset = self.__offset
                subtext = self.__text
            else:
                # use groups to calculate size if they are unchanged in lookback
                groups = None if contains_instance(next[1], StartGroup) \
                            else state.groups
                # calculate lookback size if possible
                try:
                    offset = self.__offset - \
                        next[1].size(None 
                                     if contains_instance(next[1], StartGroup)
                                     else state.groups)
                except Exception:
                    offset = 0
                    search = True
                subtext = self.__text[0:self.__offset]
            if contains_instance(next[1], ReadsGroup):
                groups = state.groups
            else:
                groups = None
            engine = ParallelEngine(self._parser_state, next[1])
            match = bool(engine.run_state(state.clone(next[1]), subtext, 
                                          pos=offset, search=search,
                                          groups=groups))
            self.ticks += engine.ticks
            self.__lookaheads[node][self.__offset] = match == equal
        # if lookahead succeeded, continue
        if self.__lookaheads[node][self.__offset]:
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
