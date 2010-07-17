
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
A replacement for Python's `re` package that uses the simple engine.
'''

from rxpy.compat.module import Re
from rxpy.engine.backtrack.engine import BacktrackingEngine

_re = Re(BacktrackingEngine, 'Backtracking')

compile = _re.compile
RegexObject = _re.RegexObject
MatchIterator = _re.MatchIterator
match = _re.match    
search = _re.search
findall = _re.findall
finditer = _re.finditer    
sub = _re.sub    
subn = _re.subn    
split = _re.split    
error = _re.error
escape = _re.escape    
Scanner = _re.Scanner    

(I, M, S, U, X, A, _L, _C, _E, _U, _G, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _LOOP_UNROLL, _CHARS, _EMPTY, _UNSAFE, _GROUPS) = _re.FLAGS
