
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


from rxpy.compat.support import compile as compile_, \
    RegexObject as RegexObject_, MatchIterator as MatchIterator_, \
    match as match_, search as search_, findall as findall_, \
    finditer as finditer_, sub as sub_, subn as subn_, \
    split as split_, error as error_, escape as escape_, Scanner as Scanner_
from rxpy.lib import _FLAGS
    

class Re(object):
    
    def __init__(self, engine, name):
        self.__engine = engine
        self.__name = name
        self.error = error_
        self.escape = escape_
        self.FLAGS = _FLAGS
        (self.I, self.M, self.S, self.U, self.X, self.A, 
         self._L, self._C, self._E, self._U, self._G, 
         self.IGNORECASE, self.MULTILINE, self.DOTALL, self.UNICODE, 
         self.VERBOSE, self.ASCII, 
         self._LOOP_UNROLL, self._CHARS, self._EMPTY, self._UNSAFE, 
         self._GROUPS) = _FLAGS

    def __str__(self):
        return self.__name

    def _engine(self, engine):
        if engine:
            return engine
        else:
            return self.__engine
        
    def compile(self, pattern, flags=None, alphabet=None, engine=None):
        return compile_(pattern, flags=flags, alphabet=alphabet,
                        engine=self._engine(engine))
                      
    @property
    def RegexObject(self):
        class RegexObject(RegexObject_):
            def __init__(inner, parsed, pattern=None, engine=None):
                super(RegexObject_, inner).__init__(
                                    parsed, pattern=pattern,
                                    engine=self._engine(engine))
        return RegexObject
    
    @property
    def MatchIterator(self):
        class MatchIterator(MatchIterator_):
            def __init__(inner, re, parsed, text, pos=0, endpos=None, 
                         engine=None):
                super(MatchIterator_, inner).__init__(
                                    re, parsed, text, pos=pos, endpos=endpos,
                                    engine=self._engine(engine))
        return MatchIterator
    
    def match(self, pattern, text, flags=0, alphabet=None, engine=None):
        return match_(pattern, text, flags=flags, alphabet=alphabet,
                      engine=self._engine(engine))
        
    def search(self, pattern, text, flags=0, alphabet=None, engine=None):
        return search_(pattern, text, flags=flags, alphabet=alphabet,
                      engine=self._engine(engine))

    def findall(self, pattern, text, flags=0, alphabet=None, engine=None):
        return findall_(pattern, text, flags=flags, alphabet=alphabet,
                        engine=self._engine(engine))

    def finditer(self, pattern, text, flags=0, alphabet=None, engine=None):
        return finditer_(pattern, text, flags=flags, alphabet=alphabet,
                         engine=self._engine(engine))
        
    def sub(self, pattern, repl, text, count=0, flags=0, alphabet=None, 
            engine=None):
        return sub_(pattern, repl, text, count=count, flags=flags, 
                    alphabet=alphabet, engine=self._engine(engine))

    def subn(self, pattern, repl, text, count=0, flags=0, alphabet=None, 
             engine=None):
        return subn_(pattern, repl, text, count=count, flags=flags, 
                     alphabet=alphabet, engine=self._engine(engine))

    def split(self, pattern, text, maxsplit=0, flags=0, alphabet=None, 
              engine=None):
        return split_(pattern, text, maxsplit=maxsplit, flags=flags, 
                      alphabet=alphabet, engine=self._engine(engine))

    @property
    def Scanner(self):
        class Scanner(Scanner_):
            def __init__(inner, pairs, flags=0, alphabet=None, engine=None):
                super(Scanner, inner).__init__(
                                    pairs, flags=flags, alphabet=alphabet, 
                                    engine=self._engine(engine))
        return Scanner
