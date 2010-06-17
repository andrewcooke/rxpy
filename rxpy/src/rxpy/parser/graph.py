

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
        

class _BaseNode(object):
    '''
    Subclasses describe ordered actions (typically, matches) to be made.
    
    This base class provides support for constructing and connecting nodes,
    cloning them, and displaying them in GraphViz.
    
    Nodes accessible from this instance are visible in `.next`.
    
    This class is designed to support both simple nodes (an instance is a
    graph node) and complex nodes (an instance describes some subset of
    the graph with a single entry node, and which will be given a single exit 
    node).  Complex nodes are used during construction of the graph (eg for 
    sequences and alternatives), but final connection of nodes connects the 
    individual sub-nodes.
    '''
    
    def __init__(self):
        '''
        Subclasses should pay attention to the relationship between 
        constructor kargs and attributes assumed in `.clone`.
        '''
        self.next = []
        
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
        
    def __str__(self):
        raise Exception(format('Missing __str__ in {0}', 
                               self.__class__.__name__))
        
    def clone(self, cache=None):
        '''
        Duplicate this node (necessary when replacing a numbered repeat with
        explicit, repeated, instances, for example).
        
        This copies all "public" attributes as constructor kargs.
        '''
        if cache is None:
            cache = {}
        copy = self.__class__(**self.__kargs())
        cache[self] = copy
        copy.next = list(self.__clone_next(cache))
        return cache[self]
        
    def __clone_next(self, cache):
        for next in self.next:
            if next not in cache:
                next.clone(cache=cache)
            yield cache[next]
        
    def __kargs(self):
        return dict((name, getattr(self, name))
                     for name in self.__dict__ 
                     if not name.startswith('_') and name != 'next')
        

class String(_BaseNode):
    '''
    Match a series of literal characters.
    '''
    
    def __init__(self, text):
        super(String, self).__init__()
        self.text = text
        
    def __str__(self):
        return self.text
    
    def visit(self, visitor, state=None):
        return visitor.string(self.next, self.text, state)


class StartGroup(_BaseNode):
    '''
    Mark the start of a group (to be saved).
    '''
    
    def __init__(self, number):
        super(StartGroup, self).__init__()
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        return "("
        
    def visit(self, visitor, state=None):
        return visitor.start_group(self.next, self.number, state)


class EndGroup(_BaseNode):
    '''
    Mark the end of a group (to be saved).
    '''
    
    def __init__(self, number):
        super(EndGroup, self).__init__()
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        return ")"
    
    def visit(self, visitor, state=None):
        return visitor.end_group(self.next, self.number, state)


class _BaseSplit(_BaseNode):
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
        super(_BaseSplit, self).__init__()
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


class Split(_BaseSplit):
    
    def __init__(self, label, lazy=False):
        super(Split, self).__init__(lazy=lazy)
        self.label = label + ('?' if lazy else '')
        
    def __str__(self):
        return self.label

    def visit(self, visitor, state=None):
        return visitor.split(self.next, state)


class Match(_BaseNode):
    
    def __str__(self):
        return 'Match'

    def visit(self, visitor, state=None):
        return visitor.match(state)


class _LineNode(_BaseNode):

    def __init__(self, multiline):
        super(_LineNode, self).__init__()
        self.multiline = multiline
    

class Dot(_LineNode):
    
    def __str__(self):
        return '.'

    def visit(self, visitor, state=None):
        return visitor.dot(self.next, self.multiline, state)


class StartOfLine(_LineNode):
    
    def __str__(self):
        return '^'
    
    def visit(self, visitor, state=None):
        return visitor.start_of_line(self.next, self.multiline, state)

    
class EndOfLine(_LineNode):
    
    def __str__(self):
        return '$'
    
    def visit(self, visitor, state=None):
        return visitor.end_of_line(self.next, self.multiline, state)


class GroupReference(_BaseNode):
    
    def __init__(self, number):
        super(GroupReference, self).__init__()
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        return '\\' + str(self.number)

    def visit(self, visitor, state=None):
        return visitor.group_reference(self.next, self.number, state)


class Lookahead(_BaseSplit):
    
    def __init__(self, equal, forwards):
        super(Lookahead, self).__init__(lazy=True)
        self.equal = equal
        self.forwards = forwards
        
    def __str__(self):
        return '(?' + \
            ('' if self.forwards else '<') + \
            ('=' if self.equal else '!') + '...)'

    def visit(self, visitor, state=None):
        return visitor.lookahead(self.next, self, self.equal, self.forwards, state)


class Repeat(_BaseNode):
    
    def __init__(self, begin, end, lazy):
        '''
        If end is None the range is open.  Note that lazy here is a flag,
        it doesn't change how the children are ordered.
        '''
        super(Repeat, self).__init__()
        self.begin = begin
        self.end = end
        self.lazy = lazy
        self.__connected = False
    
    def concatenate(self, next):
        if next:
            if self.__connected:
                raise GraphException('Node already connected')
            self.next.insert(0, next.start)
            self.__connected = True
        return self

    def __str__(self):
        text = '{' + str(self.begin)
        if self.end != self.begin:
            text += ','
            if self.end is not None:
                text += str(self.end)
        text += '}'
        if self.lazy:
            text += '?'
        return text 
    
    def visit(self, visitor, state=None):
        return visitor.repeat(self.next, self, self.begin, self.end, self.lazy, 
                              state)
    
    
class Conditional(_BaseSplit):
    '''
    If the group exists, the second child should be followed, otherwise the
    first.
    '''
    
    def __init__(self, number, lazy=True):
        super(Conditional, self).__init__(lazy=lazy)
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        text = '(?(' + str(self.number) + ')...'
        if len(self.next) == 3:
            text += '|...'
        text += ')'
        return text 
    
    def visit(self, visitor, state=None):
        return visitor.conditional(self.next, self.number, state)


class _EscapedNode(_BaseNode):
    
    def __init__(self, character, inverted=False):
        super(_EscapedNode, self).__init__()
        self._character = character
        self.inverted = inverted
        
    def __str__(self):
        return '\\' + (self._character.upper() 
                       if self.inverted else self._character.lower())
    
    
class WordBoundary(_EscapedNode):
    
    def __init__(self, inverted=False):
        super(WordBoundary, self).__init__('b', inverted)

    def visit(self, visitor, state=None):
        return visitor.word_boundary(self.next, self.inverted, state)


class Digit(_EscapedNode):
    
    def __init__(self, inverted=False):
        super(Digit, self).__init__('d', inverted)

    def visit(self, visitor, state=None):
        return visitor.digit(self.next, self.inverted, state)


class Space(_EscapedNode):
    
    def __init__(self, inverted=False):
        super(Space, self).__init__('s', inverted)

    def visit(self, visitor, state=None):
        return visitor.space(self.next, self.inverted, state)


class Word(_EscapedNode):
    
    def __init__(self, inverted=False):
        super(Word, self).__init__('w', inverted)

    def visit(self, visitor, state=None):
        return visitor.word(self.next, self.inverted, state)


