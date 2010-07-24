
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


from rxpy.lib import UnsupportedOperation, unimplemented
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
    
    def checkpoint(self, id):
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


class BaseCompiledNode(object):
    
    def __init__(self, *args, **kargs):
        super(BaseCompiled, self).__init__(*args, **kargs)
    
    def _compile_name(self):
        def with_dashes(name):
            first = True
            for letter in name:
                if letter.isupper() and not first:
                    yield '_'
                first = False
                yield letter.lower()
        return ''.join(with_dashes(self.__class__.__name__))

    @unimplemented
    def compile(self, compiled):
        pass
    
    def _compile_args(self):
        kargs = self._kargs()
        return [kargs[name] for name in sorted(kargs)]
        

class DirectCompiled(BaseCompiledNode):
    '''
    Returns next state after consuming input.  Assumes that method returns
    True on consumption and False otherwise.  Uses the stack, but is restricted
    to a finite depth by checkpointing.
    '''
    
    def compile(self, target):
        method = getattr(target, self._compile_name())
        args = self._compile_args()
        return self._make_compiler(method, args)
    
    def _make_compiler(self, method, args):
        def compiler(node_to_index, table):
            try:
                next = node_to_index[self.next[0]]
            except IndexError:
                next = None
            def compiled():
                if method(*args):
                    return next
                else:
                    return table[next]()
            return compiled
        return compiler


class TranslatedCompiled(DirectCompiled):
    '''
    Transform first arg to index
    '''
    
    @unimplemented
    def _compile_args(self):
        pass
    
    def _untranslated_args(self):
        return super(TranslatedCompiled, self)._compile_args()
    
    def _make_compiler(self, method, args):
        def compiler(node_to_index, table):
            try:
                next = node_to_index[self.next[0]]
            except IndexError:
                next = None
            args[0] = node_to_index[args[0]]
            def compiled():
                if method(*args):
                    return next
                else:
                    return table[next]()
            return compiled
        return compiler
    
    
class DirectIdCompiled(TranslatedCompiled):
    '''
    First arg is `self`, transformed to index
    '''
    
    def _compile_args(self):
        return [self] + self._untranslated_args()
    
    
class DirectNextCompiled(TranslatedCompiled):
    '''
    First arg is `next[0]`, transformed to index
    '''
    
    def _compile_args(self):
        return [self.next[0]] + self._untranslated_args()
    
    
class BranchCompiled(BaseCompiledNode):
    '''
    Expects `method` to return the required index, which is evaluated until
    input is consumed.
    '''
    
    def compile(self, target):
        method = getattr(target, self._compile_name())
        args = self._compile_args()
        def compiler(node_to_index, table):
            next = list(map(lambda node: (node_to_index[node], node), self.next))
            nargs = [next] + args
            def compiled():
                return table[next[method(*nargs)][0]]()
            return compiled
        return compiler
