
# The contents of this file are subject to the Mozilla Public License
# (MPL) Version 1.1 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License
# at http://www.mozilla.org/MPL/                                      
#                                                                     
# Software distributed under the License is distributed on an "AS IS" 
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See 
# the License for the specific language governing rights and          
# limitations under the License.                                      
#                                                                     
# The Original Code is RXPY (http://www.acooke.org/rxpy)              
# The Initial Developer of the Original Code is Andrew Cooke.         
# Portions created by the Initial Developer are Copyright (C) 2010
# Andrew Cooke (andrew@acooke.org). All Rights Reserved.               
#                                                                      
# Alternatively, the contents of this file may be used under the terms 
# of the LGPL license (the GNU Lesser General Public License,          
# http://www.gnu.org/licenses/lgpl.html), in which case the provisions 
# of the LGPL License are applicable instead of those above.           
#                                                                      
# If you wish to allow use of your version of this file only under the 
# terms of the LGPL License and not to allow others to use your version
# of this file under the MPL, indicate your decision by deleting the   
# provisions above and replace them with the notice and other provisions
# required by the LGPL License.  If you do not delete the provisions    
# above, a recipient may use your version of this file under either the 
# MPL or the LGPL License.                                              

'''
Logic related to Unicode input.
'''


from sys import maxunicode
from unicodedata import category

from rxpy.alphabet.base import Alphabet


WORD = set(['Ll', 'Lo', 'Lt', 'Lu', 'Mc', 'Me', 'Mn', 'Nd', 'Nl', 'No', 'Pc'])


class Unicode(Alphabet):
    '''
    Define character sets etc for Unicode strings.
    
    See base class for full documentation.
    '''
    
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
        Return either (True, (lo, hi)) or (False, char)
        '''
        from rxpy.parser.support import ParserState
        char = self.join(self.coerce(char))
        if flags & ParserState.IGNORECASE:
            lo = char.lower()
            hi = char.upper()
            if lo != hi:
                return (True, (lo, hi))
        return (False, char)
