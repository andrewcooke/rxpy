
from rxpy.parser.visitor import Visitor as _Visitor, UnsupportedOperation


class Fail(Exception):
    pass


class State(object):
    
    def __init__(self, stream, offset=0, groups=None, previous=None):
        self.__stream = stream
        self.__offset = 0
        self.__groups = groups if groups is not None else Groups(stream)
        self.__previous = previous
    
    def clone(self):
        return State(self.__stream, self.__offset, self.__groups.clone(),
                     self.__previous)
    
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
    
    def dot(self):
        try:
            self.__stream[0] # force error if doesn't exist
            self.__stream = self.__stream[1:]
            self.__offset += 1
            return self
        except:
            raise Fail
        
    def start_of_line(self, multiline):
        if self.__previous is None or (multiline and self.__previous == '\n'):
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
    
    def group(self, number):
        return self.__groups[number]
    

class Visitor(_Visitor):
    
    def __init__(self, alphabet, graph, stream, groups=None):
        self.__alphabet = alphabet
        self.__stream = stream
        self.__stack = []
        self.__lookaheads = {} # map from node to set of known ok states
        self.__match = None
        state = State(stream=stream, groups=groups)
        state.start_group(0)
        while self.__match is None:
            try:
                (graph, state) = graph.visit(self, state)
            except Fail:
                if self.__stack:
                    (graph, state) = self.__stack.pop()()
                else:
                    break
        if self.__match:
            state.end_group(0)
            self.groups = state.groups
        else:
            self.groups = Groups()
        
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
            return (next[0], state.string(state.groups.group(number)))
        except:
            raise Fail

    def conditional(self, next, number, state):
        try:
            state.groups.group(number)
            return (next[1], state)
        except:
            return (next[0], state)

    def split(self, next, state):
        for graph in reversed(next[1:]):
            clone = state.clone()
            self.__stack.append(lambda: (graph, clone))
        return (next[0], state)

    def match(self, state):
        self.__match = True
        return (None, state)

    def dot(self, next, multiline, state):
        return (next[0], state.dot())
    
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
                visitor = Visitor(self.__alphabet, next[1], state.stream,
                                  groups=state.groups.clone())
                self.__lookaheads[node][state.offset] = bool(visitor) == equal
            else:
                visitor = Visitor(self.__alphabet, next[1], 
                                  self.__stream[0:state.offset],
                                  groups=state.groups.clone())
                self.__lookaheads[node][state.offset] = bool(visitor) == equal
        # if lookahead succeeded, continue
        if self.__lookaheads[node][state.offset]:
            return (next[0], state)
        else:
            raise Fail

    def repeat(self, next, begin, end, state):
        raise UnsupportedOperation('repeat')
    
    def word_boundary(self, next, inverted, state):
        raise UnsupportedOperation('word_boundary')

    def digit(self, next, inverted, state):
        raise UnsupportedOperation('digit')
    
    def space(self, next, inverted, state):
        raise UnsupportedOperation('space')
    
    def word(self, next, inverted, state):
        raise UnsupportedOperation('word')
    