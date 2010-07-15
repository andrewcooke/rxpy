
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


from rxpy.lib import RxpyException


class ParseException(RxpyException):
    '''
    Identify the location of errors.
    '''
    
    def __init__(self, title, explanation):
        super(ParseException, self).__init__(title)
        self.title = title
        self.explanation = explanation
    
    def update(self, pattern, offset):
        if offset > 30:
            pattern = '...' + pattern[offset-33:]
            spaces = 30
        else:
            spaces = offset
        padding = spaces * ' '
        self.pattern = pattern
        self.offset = offset
        self.args = (
'''%s

  %s
  %s^
%s''' % (self.title, pattern, padding, self.explanation),)
        
    def __str__(self):
        try:
            return self.args[0]
        except IndexError:
            return self.title


class EmptyException(ParseException):
    '''
    Indicate that an empty expression is being repeated.  This is caught and
    converted into an EmptyException.
    '''
    
    def __init__(self):
        super(EmptyException, self).__init__('Repeated empty match.', '''
A sub-pattern that may match the empty string is being repeated.  This usually
indicates an error since an empty match can repeat indefinitely.

If you are sure that the pattern is correct then compile using the _EMPTY
flag to suppress this error; the engine will then match the empty string at
most once.

You can also suppress the "at most once" limitation with the _UNSAFE flag, but
this may result in a match that does not terminate.''')
        
        
class SimpleGroupException(ParseException):
    '''
    Indicate that group naming conventions have been broken.
    '''
    
    def __init__(self, title):
        super(SimpleGroupException, self).__init__(title, '''
By default, RXPY only allows simple, unaliased group names.  This reflects
normal Python standards and the pattern probably contains an error.

If you are sure that the pattern is correct then compile using the_GROUPS
flag to suppress this error; the engine will then allow groups to be reused
and for group indices to be non-contiguous.''')
