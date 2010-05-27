
from rxpy.parser.visitor import Visitor as _Visitor
from rxpy.parser.graph import Match


class Fail(Exception):
    pass


class Visitor(_Visitor):
    
    def __init__(self, alphabet, graph, stream):
        self.__alphabet = alphabet
        self.__stack = []
        self.__stream = stream
        while not isinstance(graph, Match):
            try:
                (graph, self.__stream) = graph.visit(self)
            except Fail:
                if self.__stack:
                    (graph, self.__stream) = self.__stack.pop()
                else:
                    raise Fail
        
    def string(self, next, text):
        try:
            l = len(text)
            if self.__stream[0:l] == text:
                return (next[0], self.__stream[l:]) 
        except:
            pass
        raise Fail
    
    def start_group(self, next, number):
        raise UnsupportedOperation('start_group')
    
    def end_group(self, next, number):
        raise UnsupportedOperation('end_group')

    def group_reference(self, next, number):
        raise UnsupportedOperation('group_reference')

    def conditional(self, next, number):
        raise UnsupportedOperation('conditional')

    def split(self, next):
        raise UnsupportedOperation('split')

    def match(self):
        raise UnsupportedOperation('match')

    def dot(self, next, multiline):
        raise UnsupportedOperation('dot')
    
    def start_of_line(self, next, multiline):
        raise UnsupportedOperation('start_of_line')
    
    def end_of_line(self, next, multiline):
        raise UnsupportedOperation('end_of_line')
    
    def lookahead(self, next, sense, forwards):
        raise UnsupportedOperation('lookahead')

    def repeat(self, next, begin, end):
        raise UnsupportedOperation('repeat')
    
    def word_boundary(self, next, inverted):
        raise UnsupportedOperation('word_boundary')

    def digit(self, next, inverted):
        raise UnsupportedOperation('digit')
    
    def space(self, next, inverted):
        raise UnsupportedOperation('space')
    
    def word(self, next, inverted):
        raise UnsupportedOperation('word')
    