
from sys import maxunicode

from rxpy.alphabet.base import Alphabet


class Unicode(Alphabet):
    
    def __init__(self):
        super(Unicode, self).__init__(0, maxunicode)
        
    def code_to_char(self, code):
        return unichr(code)
    
    def char_to_code(self, char):
        return ord(char)
        
    def coerce(self, char):
        return unicode(char)
    
    def join(self, *strings):
        return self.coerce('').join(strings)
        
    def to_str(self, char):
        '''
        Display the character.
        
        Note - this is the basis of hash and equality for intervals, so must
        be unique, repeatable, etc.
        '''
        text = repr(unicode(char))
        if text[0] == 'u':
            text = text[1:]
        return text[1:-1].replace('\\', '\\\\')

