

from rxpy.alphabet.base import Alphabet


class Digits(Alphabet):
    
    def __init__(self):
        super(Digits, self).__init__(0, 9)
        
    def code_to_char(self, code):
        return code
    
    def char_to_code(self, char):
        return int(char)
        
    def coerce(self, char):
        return int(char)
        
    def join(self, *strings):
        def flatten(list_):
            for value in list_:
                if isinstance(value, list):
                    for digit in flatten(value):
                        yield digit
                else:
                    yield value
        return list(flatten(strings))
        
    def to_str(self, char):
        '''
        Display the character.
        
        Note - this is the basis of hash and equality for intervals, so must
        be unique, repeatable, etc.
        '''
        return unicode(char)
