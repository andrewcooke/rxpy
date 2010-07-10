
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


from rxpy.lib import RxpyException, unimplemented
from rxpy.graph.support import GraphException, edge_iterator


class BaseNode(object):
    '''
    Subclasses describe ordered actions (typically, matches) to be made.
    
    Nodes accessible from this instance are visible in `.next`.
    
    For automatic cloning, subclasses should have a public attribute for each
    constructor karg (and no additional public attributes).  Note that graph
    nodes are not exposed as part of the public API - they are purely internal
    to the graph/parser stage.
    '''
    
    def __init__(self, consumes=None, size=None):
        '''
        Subclasses should pay attention to the relationship between 
        constructor kargs and attributes assumed in `.clone()`.
        
        `consumes` - a tristate flag indicating whether this node consumes 
        input (None means unknown).
        
        `size` - the amount of input consumed (None means unknown).
        '''
        if consumes is None or size is None:
            assert consumes is size, 'Inconsistent uncertainty'
        self.next = []
        self.consumes = consumes
        self.size = size
        # these fields are not passed to constructors on cloning
        self._fixed = set(['next', 'consumes', 'size'])
        
    def consumer(self, lenient):
        '''
        Does this node consume data from the input string?  This is used to
        detect errors (if False, repeating with * or + would not terminate)
        during *assembly* and, as such, relies on container classes to 
        inspect contents.
        
        `lenient` - the default value if behaviour is unknown (so when lenient,
        uncertain nodes consume; when conservative uncertain nodes do not).
        '''
        if self.consumes is None:
            return lenient
        else:
            return self.consumes
    
    def length(self, groups, known=None):
        '''
        The number of characters matched by this and subsequence nodes, if
        known, otherwise None.  Nodes must give a single, fixed number or
        None, so any loops should return None.  This is used at *runtime*
        when some groups are known.
        
        `groups` - current groups.
        
        `known` - a set of visited nodes, used to detect loops.
        '''
        if known is None:
            known = set()
        if len(self.next) == 1 and self not in known and self.size is not None:
            known.add(self)
            other = self.next[0].length(groups, known)
            if other is not None:
                return self.size + other
            
    def __repr__(self):
        '''
        Generate a description of this node and accessible children which can 
        be used to plot the graph in GraphViz.
        '''
        indices = {}
        reverse = {}
        def index(node):
            if node not in indices:
                n = len(indices)
                indices[node] = n
                reverse[n] = node
            return str(indices[node])
        def escape(node):
            text = str(node)
            text = text.replace('\n','\\n')
            return text.replace('\\', '\\\\')
        edge_indices = [(index(start), index(end)) 
                        for (start, end) in edge_iterator(self)]
        edges = [' ' + start + ' -> ' + end for (start, end) in edge_indices]
        nodes = [' ' + str(index) + ' [label="{0!s}"]'.format(escape(reverse[index]))
                 for index in sorted(reverse)]
        return 'strict digraph {{\n{0!s}\n{1!s}\n}}'.format(
                        '\n'.join(nodes), '\n'.join(edges))
        
    @unimplemented
    def __str__(self):
        '''
        Subclasses must implement something useful here, which will be 
        displayed in the graphviz node (see repr).
        '''
        
    def clone(self):
        '''
        Duplicate this node (necessary when replacing a numbered repeat with
        explicit, repeated, instances, for example).
        
        This copies all "public" attributes as constructor kargs.  The 
        `next` attribute is not cloned because cloning occurs before assembly.
        '''
        try:
            return self.__class__(**self._kargs())
        except TypeError as e:
            raise RxpyException('Error cloning {0}: {1}'.format(
                                        self.__class__.__name__, e))
        
    def _kargs(self):
        '''
        Generate a list of arguments used for cloning.  Subclasses can 
        over-ride this if necessary, but probably shouldn't (instead, they
        should have attributes that correspond to kargs).
        '''
        return dict((name, getattr(self, name))
                     for name in self.__dict__ 
                     if not name.startswith('_') and name not in self._fixed)
        
    def join(self, final):
        self.next.insert(0, final)
        return self
 
    def deep_eq(self, other):
        '''
        Used only for testing.
        '''
        for ((a, b), (c, d)) in zip(edge_iterator(self), edge_iterator(other)):
            if not a._node_eq(c) or not b._node_eq(d):
                return False
        return True
        
    def _node_eq(self, other):
        return type(self) == type(other) and self._kargs() == other._kargs()
       
    @unimplemented
    def visit(self, visitor, state=None):
        '''
        The visitor pattern - used to evaluate the graph by an interpreter,
        for example.  Calls back to the visitor via the interface described
        in `rxpy.parser.visitor.Visitor`.
        '''
        

class BaseGroupReference(BaseNode):
    
    def __init__(self, number, **kargs):
        super(BaseGroupReference, self).__init__(**kargs)
        self.number = number
        
    def resolve(self, state):
        self.number = state.index_for_name_or_count(self.number)
        

class BaseLabelledNode(BaseNode):
    
    def __init__(self, label, **kargs):
        super(BaseLabelledNode, self).__init__(**kargs)
        self.label = label
        
    def __str__(self):
        return self.label
    

class BaseLineNode(BaseNode):

    def __init__(self, multiline, **kargs):
        '''
        Note that the default value of `size` has changed from `BaseNode`.
        '''
        super(BaseLineNode, self).__init__(**kargs)
        self.multiline = multiline


class BaseEscapedNode(BaseNode):
    
    def __init__(self, character, inverted=False, **kargs):
        '''
        Note that the default value of `size` has changed from `BaseNode`.
        '''
        super(BaseEscapedNode, self).__init__(**kargs)
        self._character = character
        self.inverted = inverted
        
    def __str__(self):
        return '\\' + (self._character.upper() 
                       if self.inverted else self._character.lower())
    
    
