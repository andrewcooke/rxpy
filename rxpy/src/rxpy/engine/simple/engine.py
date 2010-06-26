from rxpy.engine.base import BaseEngine

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
A matcher implementation using a simple interpreter-based approach with the
`Visitor` interface.  State (including stacks for backtracking) is 
encapsulated in `State` while program flow uses trampolining to avoid 
exhausting the Python stack. 
'''                                    

from rxpy.graph.visitor import BaseVisitor
from rxpy.compat.groups import Groups


class Fail(Exception):
    '''
    Raised on failure.
    '''
    pass


class State(object):
    '''
    State for a particular position moment / graph position / text offset.
    '''
    
    def __init__(self, text, groups, previous=None, offset=0, loops=None):
        self.__text = text
        self.__groups = groups
        self.__previous = previous
        self.__offset = offset
        self.__loops = loops if loops else Loops()
    
    def clone(self):
        return State(self.__text, self.__groups.clone(), self.__previous, 
                     self.__offset, self.__loops.clone())
        
    def advance(self):
        '''
        Used in search to increment start point.
        '''
        if self.__text:
            self.__offset += 1
            self.__groups.start_group(0, self.__offset)
            self.__previous = self.__text[0]
            self.__text = self.__text[1:]
            return True
        else:
            return False
    
    def string(self, text):
        try:
            l = len(text)
            if self.__text[0:l] == text:
                if l:
                    self.__previous = self.__text[l-1]
                    self.__text = self.__text[l:]
                    self.__offset += l
                return self
        except IndexError:
            pass
        raise Fail
    
    def character(self, charset):
        try:
            if self.__text[0] in charset:
                self.__previous = self.__text[0]
                self.__text = self.__text[1:]
                self.__offset += 1
                return self
        except IndexError:
            pass
        raise Fail
    
    def start_group(self, number):
        self.__groups.start_group(number, self.__offset)
        return self
        
    def end_group(self, number):
        self.__groups.end_group(number, self.__offset)
        return self
    
    def increment(self, node):
        return self.__loops.increment(node)
    
    def drop(self, node):
        self.__loops.drop(node)
        return self
    
    def dot(self, multiline=True):
        try:
            if self.__text[0] and (multiline or self.__text[0] != '\n'):
                self.__previous = self.__text[0]
                self.__text = self.__text[1:]
                self.__offset += 1
                return self
        except IndexError:
            pass
        raise Fail
        
    def start_of_line(self, multiline):
        if self.__offset == 0 or (multiline and self.__previous == '\n'):
            return self
        else:
            raise Fail
            
    def end_of_line(self, multiline):
        if ((not self.__text or (multiline and self.__text[0] == '\n'))
                # also before \n at end of text
                or (self.__text and self.__text[0] == '\n' and
                    not self.__text[1:])):
            return self
        else:
            raise Fail

    @property
    def groups(self):
        return self.__groups
    
    @property
    def offset(self):
        return self.__offset

    @property
    def text(self):
        return self.__text

    @property
    def previous(self):
        return self.__previous


class Loops(object):
    '''
    Manage a nested set of indices (loops *must* be nested).
    '''
    
    def __init__(self, counts=None, order=None):
        self.__counts = counts if counts else []
        
        self.__order = order if order else {}
        
    def increment(self, node):
        if node not in self.__order:
            order = len(self.__counts)
            self.__order[node] = order
            self.__counts.append(0)
        else:
            order = self.__order[node]
            self.__counts = self.__counts[0:order+1]
            self.__counts[order] += 1
        return self.__counts[order]
    
    def drop(self, node):
        self.__counts = self.__counts[0:self.__order[node]]
        del self.__order[node]
        
    def clone(self):
        return Loops(list(self.__counts), dict(self.__order))
    

class Engine(BaseEngine, BaseVisitor):
    '''
    The interpreter.
    '''
    
    def run(self, text, pos=0, search=False):
        '''
        Execute a search.
        '''
        self.__text = text
        self.__pos = pos
        
        state = State(text[pos:],
                      Groups(text=text, count=self._parser_state.group_count, 
                             names=self._parser_state.group_names, 
                             indices=self._parser_state.group_indices),
                      offset=pos, previous=text[pos-1] if pos else None)
        
        self.__stack = None
        self.__stacks = []
        self.__lookaheads = {} # map from node to set of known ok states
        self.__match = False
        
        state.start_group(0)
        (match, state) = self.__run(self._graph, state, search=search)
        if match:
            state.end_group(0)
            return state.groups
        else:
            return Groups()
            
    def __run(self, graph, state, search=False):
        '''
        Run a sun-search.  We support multiple searches (stacks) so that we
        can invoke the same interpreter for lookaheads etc.
        '''
        self.__stacks.append(self.__stack)
        self.__stack = []
        first = True
        try:
            while first or (search and not self.__match):
                # if searching, save state for restarts
                if search:
                    (save_state, save_graph) = (state.clone(), graph)
                # do a normal match
                while not self.__match:
                    try:
                        (graph, state) = graph.visit(self, state)
                    except Fail:
                        if self.__stack:
                            (graph, state) = self.__stack.pop()
                        else:
                            break
                    except AttributeError:
                        raise
                # match has exited; handle search
                first = False
                if search and not self.__match:
                    if save_state.advance():
                        (state, graph) = (save_state, save_graph) 
                    else:
                        search = False
            # search has exited; return
            return (self.__match, state)
        finally:
            self.__stack = self.__stacks.pop()
            self.__match = False
        
    def __bool__(self):
        return bool(self.__match)
    
    def __nonzero__(self):
        return bool(self.__match)
        
    def string(self, next, text, state):
        return (next[0], state.string(text))
    
    def character(self, next, charset, state):
        return (next[0], state.character(charset))
        
    def start_group(self, next, number, state):
        return (next[0], state.start_group(number))
    
    def end_group(self, next, number, state):
        return (next[0], state.end_group(number))

    def group_reference(self, next, number, state):
        try:
            text = state.groups.group(number)
            if text is None:
                raise Fail
            elif text:
                return (next[0], state.string(text))
            else:
                return (next[0], state)
        except KeyError:
            raise Fail

    def group_conditional(self, next, number, state):
        if state.groups.group(number):
            return (next[1], state)
        else:
            return (next[0], state)

    def split(self, next, state):
        for graph in reversed(next[1:]):
            clone = state.clone()
            self.__stack.append((graph, clone))
        return (next[0], state)
    
    def match(self, state):
        self.__match = True
        return (None, state)

    def dot(self, next, multiline, state):
        return (next[0], state.dot(multiline))
    
    def start_of_line(self, next, multiline, state):
        return (next[0], state.start_of_line(multiline))
        
    def end_of_line(self, next, multiline, state):
        return (next[0], state.end_of_line(multiline))
    
    def lookahead(self, next, node, equal, forwards, state):
        if node not in self.__lookaheads:
            self.__lookaheads[node] = {}
        if state.offset not in self.__lookaheads[node]:
            # we need to match the lookahead
            if forwards:
                clone = State(state.text, state.groups.clone())
            else:
                clone = State(self.__text[0:state.offset], state.groups.clone())
            (match, clone) = self.__run(next[1], clone)
            self.__lookaheads[node][state.offset] = match == equal
        # if lookahead succeeded, continue
        if self.__lookaheads[node][state.offset]:
            return (next[0], state)
        else:
            raise Fail

    def repeat(self, next, node, begin, end, lazy, state):
        count = state.increment(node)
        # if we haven't yet reached the point where we can continue, loop
        if count < begin:
            return (next[1], state)
        # stack logic depends on laziness
        if lazy:
            # we can continue from here, but if that fails we want to restart 
            # with another loop, unless we've exceeded the count or there's
            # no text left
            # this is well-behaved with stack space
            if (end is None and state.text) \
                    or (end is not None and count < end):
                self.__stack.append((next[1], state.clone()))
            if end is None or count <= end:
                return (next[0], state.drop(node))
            else:
                raise Fail
        else:
            if end is None or count < end:
                # add a fallback so that if a higher loop fails, we can continue
                self.__stack.append((next[0], state.clone().drop(node)))
            if count == end:
                # if last possible loop, continue
                return (next[0], state.drop(node))
            else:
                # otherwise, do another loop
                return (next[1], state)
    
    def word_boundary(self, next, inverted, state):
        previous = state.previous
        try:
            current = state.text[0]
        except IndexError:
            current = None
        word = self._parser_state.alphabet.word
        boundary = word(current) != word(previous)
        if boundary != inverted:
            return (next[0], state)
        else:
            raise Fail

    def digit(self, next, inverted, state):
        try:
            if self._parser_state.alphabet.digit(state.text[0]) != inverted:
                return (next[0], state.dot())
        except IndexError:
            pass
        raise Fail
    
    def space(self, next, inverted, state):
        try:
            if self._parser_state.alphabet.space(state.text[0]) != inverted:
                return (next[0], state.dot())
        except IndexError:
            pass
        raise Fail
    
    def word(self, next, inverted, state):
        try:
            if self._parser_state.alphabet.word(state.text[0]) != inverted:
                return (next[0], state.dot())
        except IndexError:
            pass
        raise Fail
