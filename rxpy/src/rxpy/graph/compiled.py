
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


from rxpy.lib import UnsupportedOperation
from rxpy.graph.support import node_iterator


class BaseCompiled(object):
    
    # direct
    
    def string(self, text):
        raise UnsupportedOperation('string')
    
    def character(self, charset):
        raise UnsupportedOperation('character')
    
    def start_group(self, number):
        raise UnsupportedOperation('start_group')
    
    def end_group(self, number):
        raise UnsupportedOperation('end_group')
    
    def match(self):
        raise UnsupportedOperation('match')

    def no_match(self):
        raise UnsupportedOperation('no_match')

    def dot(self, multiline):
        raise UnsupportedOperation('dot')
    
    def start_of_line(self, multiline):
        raise UnsupportedOperation('start_of_line')
    
    def end_of_line(self, multiline):
        raise UnsupportedOperation('end_of_line')
    
    def word_boundary(self, inverted):
        raise UnsupportedOperation('word_boundary')

    def digit(self, inverted):
        raise UnsupportedOperation('digit')
    
    def space(self, inverted):
        raise UnsupportedOperation('space')
    
    def word(self, inverted):
        raise UnsupportedOperation('word')
    
    def checkpoint(self):
        raise UnsupportedOperation('checkpoint')

    # branch

    def group_reference(self, next, number):
        raise UnsupportedOperation('group_reference')

    def conditional(self, next, number):
        raise UnsupportedOperation('conditional')

    def split(self, next):
        raise UnsupportedOperation('split')

    def lookahead(self, equal, forwards):
        raise UnsupportedOperation('lookahead')

    def repeat(self, begin, end, lazy):
        raise UnsupportedOperation('repeat')
    

def compile(graph, compiled):
    compilers = [(node, node.compile(compiled)) for node in node_iterator(graph)]
    node_index = dict((node, index) 
                      for (index, (node, _compiler)) in enumerate(compilers))
    table = []
    for (node, compiler) in compilers:
        table.append(compiler(node_index, table))
    return table

