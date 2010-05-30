
from rxpy.parser.visitor import Visitor as _Visitor


class Fail(Exception):
    pass


class State(object):
    '''
    State for a particular position moment / graph position / stream offset.
    '''
    
    def __init__(self, stream, previous=None, offset=0, groups=None, loops=None):
        self.__stream = stream
        self.__previous = previous
        self.__offset = offset
        self.__groups = groups if groups is not None else Groups(stream)
        self.__loops = loops if loops else Loops()
    
    def clone(self):
        return State(self.__stream, self.__previous, self.__offset, 
                     self.__groups.clone(), self.__loops.clone())
    
    def string(self, text):
        try:
            l = len(text)
            if self.__stream[0:l] == text:
                if l:
                    self.__previous = self.__stream[l-1]
                    self.__stream = self.__stream[l:]
                    self.__offset += l
                return self
        except:
            pass
        raise Fail
    
    def character(self, charset):
        try:
            if self.__stream[0] in charset:
                self.__previous = self.__stream[0]
                self.__stream = self.__stream[1:]
                self.__offset += 1
                return self
        except:
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
            self.__stream[0] and (multiline or self.__stream[0] != '\n')
            self.__previous = self.__stream[0]
            self.__stream = self.__stream[1:]
            self.__offset += 1
            return self
        except:
            raise Fail
        
    def start_of_line(self, multiline):
        if self.__offset == 0 or (multiline and self.__previous == '\n'):
            return self
        else:
            raise Fail
            
    def end_of_line(self, multiline):
        if not self.__stream or (multiline and self.__stream[0] == '\n'):
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
    def stream(self):
        return self.__stream

    @property
    def previous(self):
        return self.__previous


class Groups(object):
    
    def __init__(self, stream=None, groups=None, offsets=None):
        self.__stream = stream
        self.__groups = groups if groups else {}
        self.__offsets = offsets if offsets else {}
        
    def start_group(self, number, offset):
        self.__offsets[number] = offset
        
    def end_group(self, number, offset):
        assert number in self.__offsets, 'Unopened group'
        self.__groups[number] = self.__stream[self.__offsets[number]:offset]
        del self.__offsets[number]
    
    def __len__(self):
        return len(self.__groups) - 1 if self.__groups else 0
    
    def clone(self):
        return Groups(self.__stream, dict(self.__groups), dict(self.__offsets))
    
    def __delitem__(self, number):
        del self.__groups[number]
        
    def __getitem__(self, number):
        return self.__groups[number]
    
    def __setitem(self, number, text):
        self.__groups[number] = text
    
    
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
    

class Visitor(_Visitor):
    
    def __init__(self, (alphabet, flags, graph), stream, offset=0, groups=None):
        self.__alphabet = alphabet
        self.__flags = flags
        self.__stream = stream
        self.__stack = []
        self.__lookaheads = {} # map from node to set of known ok states
        self.__match = None
        state = State(stream=stream[offset:], offset=offset, groups=groups)
        state.start_group(0)
        while self.__match is None:
            try:
                (graph, state) = graph.visit(self, state)
            except Fail:
                if self.__stack:
                    (graph, state) = self.__stack.pop()
                else:
                    break
        if self.__match:
            state.end_group(0)
            self.groups = state.groups
            self.offset = state.offset 
        else:
            self.groups = Groups()
            self.offset = None
        
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
            return (next[0], state.string(state.groups[number]))
        except KeyError:
            raise Fail

    def conditional(self, next, number, state):
        try:
            state.groups[number]
            return (next[1], state)
        except KeyError:
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
            # we need to match the lookahead, which we do as a separate process
            if forwards:
                visitor = Visitor((self.__alphabet, self.__flags, next[1]), 
                                  state.stream, groups=state.groups.clone())
                self.__lookaheads[node][state.offset] = bool(visitor) == equal
            else:
                visitor = Visitor((self.__alphabet, self.__flags, next[1]), 
                                  self.__stream[0:state.offset],
                                  groups=state.groups.clone())
                self.__lookaheads[node][state.offset] = bool(visitor) == equal
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
            # no stream left
            if (end is None and state.stream) \
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
            current = state.stream[0]
        except:
            current = None
        word = self.__alphabet.word
        boundary = word(current) != word(previous)
        if boundary != inverted:
            return (next[0], state)
        else:
            raise Fail

    def digit(self, next, inverted, state):
        try:
            if self.__alphabet.digit(state.stream[0]) != inverted:
                return (next[0], state.dot())
        except IndexError:
            pass
        raise Fail
    
    def space(self, next, inverted, state):
        try:
            if self.__alphabet.space(state.stream[0]) != inverted:
                return (next[0], state.dot())
        except IndexError:
            pass
        raise Fail
    
    def word(self, next, inverted, state):
        try:
            if self.__alphabet.word(state.stream[0]) != inverted:
                return (next[0], state.dot())
        except IndexError:
            pass
        raise Fail
