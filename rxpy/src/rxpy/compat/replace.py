
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


from rxpy.graph.visitor import BaseVisitor
from rxpy.parser.replace import parse_replace, RxpyException


class ReplVisitor(BaseVisitor):
    
    def __init__(self, repl, parser_state):
        (parser_state, self.__graph) = parse_replace(repl, parser_state)
        self.__alphabet = parser_state.alphabet
    
    def evaluate(self, match):
        self.__result = self.__alphabet.join()
        graph = self.__graph
        while graph:
            (graph, match) = graph.visit(self, match)
        return self.__result
    
    def string(self, next, text, match):
        self.__result = self.__alphabet.join(self.__result, text)
        return (next[0], match)
    
    def group_reference(self, next, number, match):
        try:
            self.__result = self.__alphabet.join(self.__result, match.group(number))
            return (next[0], match)
        # raised when match.group returns None
        except TypeError:
            raise RxpyException('No match for group ' + str(number))

    def match(self, match):
        return (None, match)


def compile_repl(repl, state):
    cache = []
    def compiled(match):
        try:
            return repl(match)
        except:
            if not cache:
                cache.append(ReplVisitor(repl, state))
        return cache[0].evaluate(match)
    return compiled

