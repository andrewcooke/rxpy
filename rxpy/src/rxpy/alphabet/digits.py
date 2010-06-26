
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
Logic related to input consiting of lists of digits (this is a proof of
concept used to test non-string inputs).
'''

from rxpy.alphabet.base import BaseAlphabet


class Digits(BaseAlphabet):
    '''
    Define character sets etc for lists of single digits.
    
    See base class for full documentation.
    '''
    
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
