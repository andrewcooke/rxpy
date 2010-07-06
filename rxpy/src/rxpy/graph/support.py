
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


from bisect import bisect_left
from collections import deque

from rxpy.lib import RxpyException, unimplemented
from traceback import print_exc


class GraphException(Exception):
    pass


def linear_iterator(node):
    '''
    Generate a sequence of nodes, taking the first child at each.
    '''
    while node:
        yield node
        node = node.next[0]
        

def edge_iterator(node):
    '''
    Generate a sequence of all the edges (as ordered node pairs) reachable
    in the graph starting from the given node.
    '''
    stack = [node]
    visited = set()
    while stack:
        node = stack.pop()
        for next in node.next:
            edge = (node, next)
            if edge not in visited:
                if next:
                    stack.append(next)
                    yield edge
                visited.add(edge)
                

def contains_instance(graph, type_):
    for (n1, n2) in edge_iterator(graph):
        if isinstance(n1, type_) or isinstance(n2, type_):
            return True
    return False
        

class BaseNode(object):
    '''
    Subclasses describe ordered actions (typically, matches) to be made.
    
    This base class provides support for constructing and connecting nodes,
    cloning them, and displaying them in GraphViz.
    
    Nodes accessible from this instance are visible in `.next`.
    
    For automatic cloning, subclasses should have a public attribute for each
    constructor karg (and no additional public attributes).  Note that graph
    nodes are not exposed as part of the public API - they are purely internal
    to RXPY.
    
    This class is designed to support both simple nodes (an instance is a
    graph node) and complex nodes (an instance describes some subset of
    the graph with a single entry node, and which will be given a single exit 
    node).  Complex nodes are used during construction of the graph (eg for 
    sequences and alternatives), but final connection of nodes connects the 
    individual sub-nodes.
    '''
    
    def __init__(self, consumer=True, size=None):
        '''
        Subclasses should pay attention to the relationship between 
        constructor kargs and attributes assumed in `.clone`.
        '''
        self.next = []
        self.__consumer = consumer
        self.__size = size
        
    @property
    def consumer(self):
        '''
        Does this node consume data from the input string?  This is used to
        detect errors (if False, repeating with * or + would not terminate).
        '''
        return self.__consumer
    
    def size(self, groups, known=None):
        '''
        The number of characters matched by this and subsequence nodes, if
        known, otherwise None.  Nodes must give a single, fixed number or
        None, so any loops should return None.
        '''
        if known is None:
            known = set()
        if len(self.next) == 1 and self not in known and self.__size is not None:
            known.add(self)
            other = self.next[0].size(groups, known)
            if other is not None:
                return self.__size + other
            
    @property
    def start(self):
        '''
        The node to connect to when connecting to "this" node.  For a simple
        node, this is simply 'self', but for a complex node (one that contains
        sub-nodes) this method must return the "entry node".
        
        This method is only called on complex nodes after "initial node
        assembly" is complete (complex nodes are assembled, then connected).
        '''
        return self
    
    def concatenate(self, next):
        '''
        The given node is the next node in the sequence.
        
        This method is only called on complex nodes after "initial node
        assembly" is complete (complex nodes are assembled, then connected).
        It is also only called once.
        '''
        if next:
            if self.next:
                raise GraphException('Node already connected')
            self.next = [next.start]
        return self
    
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
        
    def clone(self, cache=None):
        '''
        Duplicate this node (necessary when replacing a numbered repeat with
        explicit, repeated, instances, for example).
        
        This copies all "public" attributes as constructor kargs.
        '''
        if cache is None:
            cache = {}
        try:
            copy = self.__class__(**self._kargs())
        except TypeError as e:
            raise RxpyException('Error cloning {0}: {1}'.format(
                                        self.__class__.__name__, e))
        cache[self] = copy
        copy.next = list(self.__clone_next(cache))
        return cache[self]
        
    def __clone_next(self, cache):
        '''
        Clone child nodes, using the cache where appropriate.
        '''
        for next in self.next:
            if next not in cache:
                next.clone(cache=cache)
            yield cache[next]
            
    def _node_eq(self, other):
        return type(self) == type(other) and self._kargs() == other._kargs()
    
    def deep_eq(self, other):
        '''
        Used only for testing.
        '''
        for ((a, b), (c, d)) in zip(edge_iterator(self), edge_iterator(other)):
            if not a._node_eq(c) or not b._node_eq(d):
                return False
        return True
        
    def _kargs(self):
        '''
        Generate a list of arguments used for cloning.  Subclasses can 
        over-ride this if necessary, but probably shouldn't (instead, they
        should have attributes that correspond to kargs).
        '''
        return dict((name, getattr(self, name))
                     for name in self.__dict__ 
                     if not name.startswith('_') and name != 'next')
        
    @unimplemented
    def visit(self, visitor, state=None):
        '''
        The visitor pattern - used to evaluate the graph by an interpreter,
        for example.  Calls back to the visitor via the interface described
        in `rxpy.parser.visitor.Visitor`.
        '''
        

class BaseSplitNode(BaseNode):
    '''
    Base class for any node that includes a "tee".
    
    Note that a continuation node is added via concatenate.  In other words,
    when used within a Sequence, this node will, in addition to providing
    a branch, also connect directly to the following node.  So only "extra"
    branches need to be provided directly by subclasses.
    
    To rejoin the branch, use `Merge()`.
    
    The lazy flag controls the position of the following node; if False the
    node is appended to the list of child nodes, otherwise it is inserted
    into the first position.  This implies that evaluation should prefer
    children in the order given. 
    '''
    
    def __init__(self, lazy=False):
        super(BaseSplitNode, self).__init__()
        self.lazy = lazy
        self.__connected = False
        
    def concatenate(self, next):
        if next:
            if self.__connected:
                raise GraphException('Node already connected: ' + 
                                     self.__class__.__name__)
            if self.lazy:
                self.next.insert(0, next.start)
            else:
                self.next.append(next.start)
            self.__connected = True
        return self
    
    
class ReadsGroup(object):
    '''
    Used to identify opcdes that require groups.
    '''


class BaseLineNode(BaseNode):

    def __init__(self, multiline, consumer=False, size=0):
        '''
        Note that the default value of `size` has changed from `BaseNode`.
        '''
        super(BaseLineNode, self).__init__(consumer=consumer, size=size)
        self.multiline = multiline
    

class BaseEscapedNode(BaseNode):
    
    def __init__(self, character, inverted=False, consumer=True, size=1):
        '''
        Note that the default value of `size` has changed from `BaseNode`.
        '''
        super(BaseEscapedNode, self).__init__(consumer=consumer, size=size)
        self._character = character
        self.inverted = inverted
        
    def __str__(self):
        return '\\' + (self._character.upper() 
                       if self.inverted else self._character.lower())
    
    
class CharSet(object):
    '''
    A set of possible values for a character, described as a collection of 
    intervals.  Each interval is [a, b] (ie a <= x <= b, where x is a character 
    code).  We use open bounds to avoid having to specify an "out of range"
    value.
    
    The intervals are stored in a normalised list, ordered by a, joining 
    overlapping intervals as necessary.
    
    [This is based on lepl.regexp.interval.Character]
    '''
    
    # pylint: disable-msg=C0103 
    # (use (a,b) variables consistently)
    
    def __init__(self, intervals, alphabet):
        self.intervals = deque()
        self.__index = None
        self.__str = None
        for interval in intervals:
            self.append(interval, alphabet)
        
    def append(self, interval, alphabet):
        '''
        Add an interval to the existing intervals.
        
        This maintains self.intervals in the normalized form described above.
        '''
        self.__index = None
        self.__str = None
        
        (a1, b1) = map(alphabet.coerce, interval)
        if b1 < a1:
            (a1, b1) = (b1, a1)
        intervals = deque()
        done = False
        while self.intervals:
            # pylint: disable-msg=E1103
            # (pylint fails to infer type)
            (a0, b0) = self.intervals.popleft()
            if a0 <= a1:
                if b0 < a1 and b0 != alphabet.before(a1):
                    # old interval starts and ends before new interval
                    # so keep old interval and continue
                    intervals.append((a0, b0))
                elif b1 <= b0:
                    # old interval starts before and ends after new interval
                    # so keep old interval, discard new interval and slurp
                    intervals.append((a0, b0))
                    done = True
                    break
                else:
                    # old interval starts before new, but partially overlaps
                    # so discard old interval, extend new interval and continue
                    # (since it may overlap more intervals...)
                    (a1, b1) = (a0, b1)
            else:
                if b1 < a0 and b1 != alphabet.before(a0):
                    # new interval starts and ends before old, so add both
                    # and slurp
                    intervals.append((a1, b1))
                    intervals.append((a0, b0))
                    done = True
                    break
                elif b0 <= b1:
                    # new interval starts before and ends after old interval
                    # so discard old and continue (since it may overlap...)
                    pass
                else:
                    # new interval starts before old, but partially overlaps,
                    # add extended interval and slurp rest
                    intervals.append((a1, b0))
                    done = True
                    break
        if not done:
            intervals.append((a1, b1))
        intervals.extend(self.intervals) # slurp remaining
        self.intervals = intervals
        
    def __contains__(self, c):
        '''
        Does the value lie within the intervals?
        '''
        if self.__index is None:
            self.__index = [interval[1] for interval in self.intervals]
        if self.__index:
            index = bisect_left(self.__index, c)
            if index < len(self.intervals):
                (a, b) = self.intervals[index]
                return a <= c <= b
        return False
    
    def __format_interval(self, interval, alphabet):
        (a, b) = interval
        if a == b:
            return alphabet.to_str(a)
        elif a == alphabet.before(b):
            return alphabet.to_str(a) + alphabet.to_str(b)
        else:
            return alphabet.to_str(a) + '-' + alphabet.to_str(b)

    def to_str(self, alphabet):
        if self.__str is None:
            self.__str = ''.join(map(lambda x: self.__format_interval(x, alphabet), 
                                     self.intervals))
        return self.__str

    def simplify(self, alphabet, default):
        from rxpy.graph.opcode import String, Dot
        if len(self.intervals) == 1:
            if self.intervals[0][0] == self.intervals[0][1]:
                return String(self.intervals[0][0])
            elif self.intervals[0][0] == alphabet.min and \
                    self.intervals[0][1] == alphabet.max:
                return Dot(True)
        return default
    
    def __bool__(self):
        return bool(self.intervals)
    
    def __nonzero__(self):
        return self.__bool__()
