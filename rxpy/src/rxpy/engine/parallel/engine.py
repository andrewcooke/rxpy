from rxpy.lib import _STRINGS, UnsupportedOperation

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


class State(object):
    '''
    State for a particular thread (offset in the text is common to all threads).
    '''
    
    def __init__(self, graph, groups=None, loops=None, **groups_kargs):
        self.__graph = graph
        self.__groups = groups if groups is not None else [None, None, groups_kargs]
        self.__loops = loops
        self.match = False
        
    def clone(self):
        try:
            groups = self.__groups.clone()
        except AttributeError:
            groups = list(self.__groups)
        try:
            loops = self.__loops.clone()
        except AttributeError:
            loops = self.__loops
        return State(self.__graph, groups=groups, loops=loops)
    
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
        self.__text = text
        self.__offset = pos
        
        state = State(self._graph,
                      text=text, count=self._parser_state.group_count, 
                      names=self._parser_state.group_names, 
                      indices=self._parser_state.group_indices)
        state.start_group(0, self.__offset)
        
        current_states, next_states  = [state], []

        while current_states and not current_states[-1].match:
            try:
                self.__previous = self.__text[self.__offset-1]
            except IndexError:
                self.__previous = None
            while current_states:
                state = current_states.pop()
                (updated, extra) = state.graph.visit(self, state)
                if updated:
                    next_states.append(updated)
                # we process extra states immediately
                current_states.extend(extra)
            current_states, next_states = next_states, []
            current_states.reverse()
            self.__offset += 1
        
        if current_states:
            return current_states[-1].groups
        else:
            return Groups()
        
    # below are the visitor methods - these implement the different opcodes
    # (typically by modifying state and returning the next node) 
        
    def string(self, next, text, state):
        try:
            if self.__text[self.__offset] == text:
                return (state.advance(), [])
        except IndexError:
            pass
        return (None, [])
    
    def character(self, next, charset, state):
        try:
            if self.__text[self.__offset] in charset:
                return (state.advance(), [])
        except IndexError:
            pass
        return (None, [])
    
    def start_group(self, next, number, state):
        return (None, [state.start_group(number, self.__offset).advance()])
    
    def end_group(self, next, number, state):
        return (None, [state.end_group(number, self.__offset).advance()])

    def group_reference(self, next, number, state):
        raise UnsupportedOperation

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
        try:
            if self.__text[self.__offset] and \
                    (multiline or self.__text[self.__offset] != '\n'):
                return (state.advance(), [])
        except IndexError:
            pass
        return (None, [])
        
    def start_of_line(self, next, multiline, state):
        if self.__offset == 0 or (multiline and self.__previous == '\n'):
            return (None, [state.advance()])
        else:
            return (None, [])
            
    def end_of_line(self, next, multiline, state):
        try:
            if ((len(self.__text) == self.__offset or 
                        (multiline and self.__text[self.__offset] == '\n'))
                    or (self.__text and self.__text[0] == '\n' and
                            not self.__text[1:])):
                return (None, [state.advance()])
        except IndexError:
            pass
        return (None, [])
        
    def lookahead(self, next, node, equal, forwards, state):
        raise UnsupportedOperation

    def repeat(self, next, node, begin, end, lazy, state):
        raise UnsupportedOperation
    
    def word_boundary(self, next, inverted, state):
        try:
            current = self.__text[self.__offset]
        except IndexError:
            current = None
        word = self._parser_state.alphabet.word
        boundary = word(current) != word(self.__previous)
        if boundary != inverted:
            return (None, [state.advance()])
        else:
            return (None, [])

    def digit(self, next, inverted, state):
        try:
            if self._parser_state.alphabet.digit(self.__text[self.__offset]) != inverted:
                return (state.advance(), [])
        except IndexError:
            pass
        return (None, [])
    
    def space(self, next, inverted, state):
        try:
            if self._parser_state.alphabet.space(self.__text[self.__offset]) != inverted:
                return (state.advance(), [])
        except IndexError:
            pass
        return (None, [])
    
    def word(self, next, inverted, state):
        try:
            if self._parser_state.alphabet.word(self.__text[self.__offset]) != inverted:
                return (state.advance(), [])
        except IndexError:
            pass
        return (None, [])
