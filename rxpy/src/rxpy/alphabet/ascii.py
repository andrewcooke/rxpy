
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
Logic related to ASCII input.
'''

from string import digits, ascii_letters

from rxpy.alphabet.base import Alphabet
from rxpy.lib import RxpyException


WORD = set(ascii_letters + digits + '_')


class Ascii(Alphabet):
    '''
    Define character sets etc for ASCII strings.  We could maybe extend or
    subclass this for Locale-dependent logic.
    
    See base class for full documentation.
    '''
        
    def __init__(self):
        super(Ascii, self).__init__(0, 127)
        
    def code_to_char(self, code):
        return chr(code)
    
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
        Return either (True, (lo, hi)) or (False, char)
        '''
        from rxpy.parser.parser import ParserState
        char = self.join(self.coerce(char))
        if flags & ParserState.IGNORECASE:
            lo = char.lower()
            hi = char.upper()
            if lo != hi:
                return (True, (lo, hi))
        return (False, char)
    
    def unescape(self, code):
        # for compatability with python...
        if code < 512:
            return self.code_to_char(code % 256)
        else:
            raise RxpyException('Unexpected character code for ASCII: ' + str(code)) 
