
from string import digits, ascii_letters

from rxpy.alphabet.base import Alphabet, CharSet


WORD = set(ascii_letters + digits + '_')


class Ascii(Alphabet):
    '''
    Note that this uses Unicode to encode the ASCII data (in other words,
    it's just the Unicode points 0-127).
    '''
    
    def __init__(self):
        super(Ascii, self).__init__(0, 127)
        
    def code_to_char(self, code):
        return chr(code % 256)
    
    def char_to_code(self, char):
        return ord(char)
        
    def coerce(self, char):
        return str(char)
    
    def join(self, *strings):
        return self.coerce('').join(strings)
        
    def to_str(self, char):
        '''
        Display the character.
        
        Note - this is the basis of hash and equality for intervals, so must
        be unique, repeatable, etc.
        '''
        return repr(char)[1:-1]

    def digit(self, char):
        return char in digits
    
    def space(self, char):
        return char in ' \t\n\r\f\v'
        
    def word(self, char):
        return char in WORD
    
    def unpack(self, char, flags):
        '''
        Return either (True, CharSet) or (False, char)
        '''
        from rxpy.parser.parser import ParserState
        char = self.join(self.coerce(char))
        if flags & ParserState.IGNORECASE:
            lo = char.lower()
            hi = char.upper()
            if lo != hi:
                return (True, CharSet([(lo,lo),(hi,hi)]))
        return (False, char)
