
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
`Visitor` interface.  State is encapsulated in `State` while program flow 
uses trampolining to avoid exhausting the Python stack.  In addition, to
further reduce the use of the (non-Python) stack, simple repetition is
"run length" compressed (this addresses ".*" matching against long strings, 
for example). 
'''                                    

from rxpy.engine.base import BaseEngine
from rxpy.engine.support import Groups, lookahead_logic, Loops
from rxpy.graph.visitor import BaseVisitor


class Fail(Exception):
    '''
    Raised on failure.
    '''
    pass


class Match(Exception):
    '''
    Raised on success
    '''
    pass


class State(object):
    '''
    State for a particular position moment / graph position / text offset.
    '''
    
    def __init__(self, text, groups, previous=None, offset=0, loops=None,
                 check_points=None):
        self.__text = text
        self.__groups = groups
        self.__previous = previous
        self.__offset = offset
        self.__loops = loops if loops else Loops()
        self.__check_points = check_points
    
    def clone(self, offset=None, groups=None):
        '''
        Duplicate this state.  If offset is specified, it must be greater than
        or equal the existing offset; then the text and offset of the clone
        will be consistent with the new value.  If groups is given it replaces
        the previous groups.
        '''
        if groups is None:
            groups = self.__groups.clone()
        previous = self.__previous
        if offset is None:
            offset = self.__offset
            text = self.__text
        else:
            delta = offset - self.__offset
            if delta:
                previous = self.__text[delta-1]
            text = self.__text[delta:]
        check_points = set(self.__check_points) if self.__check_points else None
        return State(text, groups, previous=previous, offset=offset, 
                     loops=self.__loops.clone(), check_points=check_points)
        
    def advance(self):
        '''
        Used in search to increment start point.
        '''
        if self.__text:
            self.__increment()
            self.__groups.start_group(0, self.__offset)
            return True
        else:
            return False
        
    def __increment(self, length=1):
        '''
        Increment offset during match.
        '''
        if length:
            self.__check_points = None
            self.__previous = self.__text[length-1]
            self.__text = self.__text[length:]
            self.__offset += length
    
    # below are methods that correspond roughly to opcodes in the graph.
    # these are called from the visitor.
        
    def string(self, text):
        try:
            l = len(text)
            if self.__text[0:l] == text:
                self.__increment(l)
                return self
        except IndexError:
            pass
        raise Fail
    
    def character(self, charset):
        try:
            if self.__text[0] in charset:
                self.__increment()
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
                self.__increment()
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
        
    def similar(self, other):
        '''
        Is this state similar to the one given?  In particular, are the
        groups and loops values identical (so we only differ by offset)?
        '''
        return self.__groups == other.__groups and self.__loops == other.__loops
    
    def check_point(self, token):
        if self.__check_points is None:
            self.__check_points = set([token])
        else:
            if token in self.__check_points:
                raise Fail
        return self

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
    
    
class Stack(object):
    '''
    A stack of states.  This extends a simple stack with the ability to 
    compress repeated states (which is useful to avoid filling the stack
    with backtracking when something like ".*" is used to match a large 
    string).
    
    The compression is quite simple: if a state and group are pushed to
    the stack which are identical, apart from offset, with the existing top
    of the stack, then the stack is not extended.  Instead, the new offset
    and increment are appended to the existing entry.  The same occurs for
    further pushes that have the same increment.
    
    On popping we create a new state, and adjust the offset as necessary.
    
    For this to work correctly we must also be careful to preserve the
    original state, since that is the one that contains the most text.
    Later states have less text and so cannot be cloned "back" to having
    an earlier offset.
    '''
    
    def __init__(self):
        self.__stack = []
        self.maxdepth = 0  # for tests
        
    def push(self, graph, state):
        if self.__stack:
            (p_graph, p_state, p_repeat) = self.__stack[-1]
            # is compressed repetition possible?
            if p_state.similar(state) and p_graph == graph:
                # do we have an existing repeat?
                if p_repeat:
                    (end, step) = p_repeat
                    # and this new state has the expected increment
                    if state.offset == end + step:
                        self.__stack.pop()
                        self.__stack.append((graph, p_state,
                                             (state.offset, step)))
                        return
                # otherwise, start a new repeat block
                elif p_state.offset < state.offset:
                    self.__stack.pop()
                    self.__stack.append((graph, p_state, 
                                         (state.offset, state.offset - p_state.offset)))
                    return
        # above returns on success, so here default to a "normal" push
        self.__stack.append((graph, state, None))
        self.maxdepth = max(self.maxdepth, len(self.__stack))
        
    def pop(self):
        (graph, state, repeat) = self.__stack.pop()
        if repeat:
            (end, step) = repeat
            # if the repeat has not expired
            if state.offset != end:
                # add back one step down
                self.__stack.append((graph, state, (end-step, step)))
                state = state.clone(end)
        return (graph, state)
            
    
    def __bool__(self):
        return bool(self.__stack)
    
    def __nonzero__(self):
        return self.__bool__()
    

class BacktrackingEngine(BaseEngine, BaseVisitor):
    '''
    The interpreter.
    '''
    
    def __init__(self, parser_state, graph):
        super(BacktrackingEngine, self).__init__(parser_state, graph)
    
    def run(self, text, pos=0, search=False):
        '''
        Execute a search.
        '''
        self.__text = text
        self.__pos = pos
        
        state = State(text[pos:],
                      Groups(group_state=self._parser_state.groups, text=text),
                      offset=pos, previous=text[pos-1] if pos else None)

        # for testing optimizations
        self.ticks = 0
        self.maxdepth = 0 
        
        self.__stack = None
        self.__stacks = []
        self.__lookaheads = {} # map from node to set of known ok states
        
        state.start_group(0)
        (match, state) = self.__run(self._graph, state, search=search)
        if match:
            state.end_group(0)
            return state.groups
        else:
            return Groups()
            
    def __run(self, graph, state, search=False):
        '''
        Run a sub-search.  We support multiple searches (stacks) so that we
        can invoke the same interpreter for lookaheads etc.
        
        This is a simple trampoline - it stores state on a stack and invokes
        the visitor interface on each graph node.  Visitor methods return 
        either the new node and state, or raise `Fail` on failure, or
        `Match` on success.
        '''
        self.__stacks.append(self.__stack)
        self.__stack = Stack()
        try:
            try:
                # search loop
                while True:
                    # if searching, save state for restart
                    if search:
                        (save_state, save_graph) = (state.clone(), graph)
                    # trampoline loop
                    while True:
                        self.ticks += 1
                        try:
                            (graph, state) = graph.visit(self, state)
                        # backtrack if stack exists
                        except Fail:
                            if self.__stack:
                                (graph, state) = self.__stack.pop()
                            else:
                                break
                    # nudge search forwards and try again, or exit
                    if search:
                        if save_state.advance():
                            (state, graph) = (save_state, save_graph)
                        else:
                            break
                    # match (not search), so exit with failure
                    else:
                        break
                return (False, state)
            except Match:
                return (True, state)
        finally:
            # restore state so that another run can resume
            self.maxdepth = max(self.maxdepth, self.__stack.maxdepth)
            self.__stack = self.__stacks.pop()
            self.__match = False
            
    # below are the visitor methods - these implement the different opcodes
    # (typically by modifying state and returning the next node) 
        
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
            self.__stack.push(graph, clone)
        return (next[0], state)
    
    def match(self, state):
        raise Match

    def dot(self, next, multiline, state):
        return (next[0], state.dot(multiline))
    
    def start_of_line(self, next, multiline, state):
        return (next[0], state.start_of_line(multiline))
        
    def end_of_line(self, next, multiline, state):
        return (next[0], state.end_of_line(multiline))
    
    def lookahead(self, next, node, equal, forwards, state):
        if node not in self.__lookaheads:
            self.__lookaheads[node] = {}
        if state.offset in self.__lookaheads[node]:
            reads, mutates = False, False
            success = self.__lookaheads[node][state.offset]
        else:
            (reads, mutates, size) = lookahead_logic(next[1], forwards, state.groups)
            search = False
            if forwards:
                clone = State(state.text, state.groups.clone())
            else:
                if size is not None and size > state.offset and equal:
                    raise Fail
                elif size is None or size > state.offset:
                    subtext = self.__text[0:state.offset]
                    previous = None
                    search = True
                else:
                    offset = state.offset - size
                    subtext = self.__text[offset:state.offset]
                    if offset:
                        previous = self.__text[offset-1]
                    else:
                        previous = None
                clone = State(subtext, state.groups.clone(), previous=previous)
            (match, clone) = self.__run(next[1], clone, search=search)
            success = match == equal
            if not (reads or mutates):
                self.__lookaheads[node][state.offset] = success
        # if lookahead succeeded, continue
        if success:
            if mutates:
                state = state.clone(groups=clone.groups)
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
                self.__stack.push(next[1], state.clone())
            if end is None or count <= end:
                return (next[0], state.drop(node))
            else:
                raise Fail
        else:
            if end is None or count < end:
                # add a fallback so that if a higher loop fails, we can continue
                self.__stack.push(next[0], state.clone().drop(node))
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

    def check_point(self, next, token, state):
        return (next[0], state.check_point(token))