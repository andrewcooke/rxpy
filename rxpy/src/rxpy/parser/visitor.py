

class UnsupportedOperation(Exception):
    pass


class Visitor(object):
    
    def string(self, next, text):
        raise UnsupportedOperation('string')
    
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
