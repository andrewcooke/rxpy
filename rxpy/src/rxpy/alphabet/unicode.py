
from sys import maxunicode
from unicodedata import category

from rxpy.alphabet.base import Alphabet, CharSet


WORD = set(['Ll', 'Lo', 'Lt', 'Lu', 'Mc', 'Me', 'Mn', 'Nd', 'Nl', 'No', 'Pc'])


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
        return text[1:-1]

    def digit(self, char):
        # http://bugs.python.org/issue1693050
        return char and category(self.coerce(char)) == 'Nd'

    def space(self, char):
        # http://bugs.python.org/issue1693050
        if char:
            c = self.coerce(char)
            return c in u' \t\n\r\f\v' or category(c) == 'Z'
        else:
            return False
        
    def word(self, char):
        # http://bugs.python.org/issue1693050
        return char and category(self.coerce(char)) in WORD
    
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
