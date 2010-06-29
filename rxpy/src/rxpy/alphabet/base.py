
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
Base class for alphabets.
'''

from rxpy.lib import UnsupportedOperation, unimplemented, RxpyException


class BaseAlphabet(object):
    '''
    Defines the interface that all alphabets must implement.
    
    An alphabet assumes that there's a mapping between "characters" and 
    integers, such that each character maps to a separate value in a 
    contiguous region between `min` and `max`.  This defines an ordering that
    is used, for example, to infer the content of character ranges.
    '''
    
    def __init__(self, min, max):
        '''
        min and max define the range of values that `char_to_code` will map
        characters to (inclusive). 
        '''
        self.min = min
        self.max = max
        
    def deep_eq(self, other):
        '''
        Used only for testing.
        '''
        return type(self) == type(other)
        
    @unimplemented
    def code_to_char(self, code):
        '''
        Convert a code - an integer value between min and max, that maps the
        alphabet to a contiguous set of integers - to a character in the
        alphabet.
        '''
    
    @unimplemented
    def char_to_code(self, char):
        '''
        Convert a character in the alphabet to a code - an integer value 
        between min and max, that maps the alphabet to a contiguous set of 
        integers.
        '''
        
    @unimplemented
    def coerce(self, char):
        '''
        Force a character in str, unicode, or the alphabet itself, to be a
        member of the alphabet. 
        '''
        
    @unimplemented
    def join(self, *strings):
        '''
        Construct a word in the alphabet, given a list of words and/or 
        characters.
        '''
        
    @unimplemented
    def to_str(self, char):
        '''
        Support display of the character.
        
        Note - this is the basis of hash and equality for intervals, so must
        be unique, repeatable, etc.
        '''
        
    def after(self, char):
        '''
        The character "before" the given one, or None
        '''
        code = self.char_to_code(char)
        if code < self.max:
            return self.code_to_char(code + 1)
        else:
            return None

    def before(self, char):
        '''
        The character "before" the given one, or None
        '''
        code = self.char_to_code(char)
        if code > self.min:
            return self.code_to_char(code - 1)
        else:
            return None
        
    def digit(self, char):
        '''
        Test whether the character is a digit or not.
        '''
        raise UnsupportedOperation('digit')
    
    def space(self, char):
        '''
        Test whether the character is a whitespace or not.
        '''
        raise UnsupportedOperation('space')
        
    def word(self, char):
        '''
        Test whether the character is a word character or not.
        '''
        raise UnsupportedOperation('word')
    
    def unpack(self, char, flags):
        '''
        Return either (True, CharSet) or (False, char)
        '''
        from rxpy.parser.support import ParserState
        if flags & ParserState.IGNORECASE:
            raise RxpyException('Default alphabet does not handle case')
        return (False, self.join(self.coerce(char)))
    
    def unescape(self, code):
        '''
        By default, assume escape codes map to character codes.
        '''
        return self.code_to_char(code)
    
    
