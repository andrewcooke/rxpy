

class Visitor(object):
    
    def string(self, next, text):
        pass
    
    def start_group(self, next, number):
        pass
    
    def end_group(self, next, number):
        pass

    def group_reference(self, next, number):
        pass

    def conditional(self, next, number):
        pass

    def split(self, next):
        pass

    def match(self):
        pass

    def dot(self, next, multiline):
        pass
    
    def start_of_line(self, next, multiline):
        pass
    
    def end_of_line(self, next, multiline):
        pass
    
    def lookahead(self, next, sense, forwards):
        pass

    def repeat(self, next, begin, end):
        pass
    
    def word_boundary(self, next, inverted):
        pass

    def digit(self, next, inverted):
        pass
    
    def space(self, next, inverted):
        pass
    
    def word(self, next, inverted):
        pass
