
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



class UnsupportedOperation(Exception):
    '''
    Raised when some (hopefully optional) functionality is not supported.
    '''


class UnimplementedMethod(Exception):
    '''
    Raised when an "abstract" method is not implemented.
    '''


def unimplemented(method):
    def replacement(*args, **kargs):
        raise UnimplementedMethod(method)
    return replacement


class RxpyException(Exception):
    '''
    General exception raised by all modules.
    '''
    
    
(I, M, S, U, X, A, _L, _C, _E, _U) = map(lambda x: 2**x, range(10))
(IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _LOOP_UNROLL, _CHARS, _EMPTY, _UNSAFE) = (I, M, S, U, X, A, _L, _C, _E, _U)
_FLAGS = (I, M, S, U, X, A, _L, _C, _E, _U, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _LOOP_UNROLL, _CHARS, _EMPTY, _UNSAFE)

FLAG_NAMES = {I: 'I/IGNORECASE',
              M: 'M/MULTILINE',
              S: 'S/DOTALL',
              U: 'U/UNICODE',
              X: 'X/VERBOSE',
              A: 'A/ASCII',
              _L: '_L/_LOOP_UNROLL',
              _C: '_C/_CHARS',
              _E: '_E/_EMPTY',
              _U: '_U/_UNSAFE'}

def refuse_flags(flags):
    names = [FLAG_NAMES[key] for key in FLAG_NAMES if key & flags]
    if names:
        raise RxpyException('Bad flag' + ('s' if len(names) > 1 else '') 
                            + ': ' + '; '.join(names))
