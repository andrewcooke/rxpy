

class UnsupportedOperation(Exception):
    pass


class Visitor(object):
    
    def string(self, next, text, state=None):
        raise UnsupportedOperation('string')
    
    def character(self, next, charset, state=None):
        raise UnsupportedOperation('character')
    
    def start_group(self, next, number, state=None):
        raise UnsupportedOperation('start_group')
    
    def end_group(self, next, number, state=None):
        raise UnsupportedOperation('end_group')

    def group_reference(self, next, number, state=None):
        raise UnsupportedOperation('group_reference')

    def conditional(self, next, number, state=None):
        raise UnsupportedOperation('conditional')

    def split(self, next, state=None):
        raise UnsupportedOperation('split')

    def match(self, state=None):
        raise UnsupportedOperation('match')

    def dot(self, next, multiline, state=None):
        raise UnsupportedOperation('dot')
    
    def start_of_line(self, next, multiline, state=None):
        raise UnsupportedOperation('start_of_line')
    
    def end_of_line(self, next, multiline, state=None):
        raise UnsupportedOperation('end_of_line')
    
    def lookahead(self, next, node, equal, forwards, state=None):
        raise UnsupportedOperation('lookahead')

    def repeat(self, next, node, begin, end, lazy, state=None):
        raise UnsupportedOperation('repeat')
    
    def word_boundary(self, next, inverted, state=None):
        raise UnsupportedOperation('word_boundary')

    def digit(self, next, inverted, state=None):
        raise UnsupportedOperation('digit')
    
    def space(self, next, inverted, state=None):
        raise UnsupportedOperation('space')
    
    def word(self, next, inverted, state=None):
        raise UnsupportedOperation('word')
