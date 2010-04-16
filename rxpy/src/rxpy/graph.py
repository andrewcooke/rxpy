

class GraphException(Exception):
    pass


def linear_iterator(node):
    while node:
        yield node
        node = node.next[0]
        

def edge_iterator(node):
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
    
    def __init__(self):
        self.next = []
        
    def __iter__(self):
        return linear_iterator(self)
    
    @property
    def start(self):
        return self
    
    def concatenate(self, next):
        if next:
            if self.next:
                raise GraphException('Node already connected')
            self.next = [next.start]
        return self
    
    def __repr__(self):
        indices = {}
        reverse = {}
        def index(node):
            if node not in indices:
                n = len(indices)
                indices[node] = n
                reverse[n] = node
            return str(indices[node])
        edge_indices = [(index(start), index(end)) 
                        for (start, end) in edge_iterator(self)]
        edges = [' ' + start + ' -> ' + end for (start, end) in edge_indices]
        nodes = [' ' + str(index) + ' [label="{0!s}"]'.format(reverse[index])
                 for index in sorted(reverse)]
        return 'strict digraph {{\n{0!s}\n{1!s}\n}}'.format(
                        '\n'.join(nodes), '\n'.join(edges))
        
    def clone(self, cache=None):
        if cache is None:
            cache = {}
        copy = self.__class__(**self.__kargs())
        copy.next = list(self.__clone_next(cache))
        return copy
        
    def __clone_next(self, cache):
        for next in self.next:
            if next not in cache:
                cache[next] = next.clone(cache=cache)
            yield cache[next]
        
    def __kargs(self):
        return dict((name, getattr(self, name))
                     for name in self.__dict__ 
                     if not name.startswith('_') and name != 'next')
        

class _AlphabetNode(_BaseNode):
    
    def __init__(self, alphabet):
        super(_AlphabetNode, self).__init__()
        self.alphabet = alphabet
    

class String(_AlphabetNode):
    
    def __init__(self, text, alphabet):
        super(String, self).__init__(alphabet)
        self.text = text
        
    def __str__(self):
        return self.alphabet.to_str(self.text)


class StartGroup(_BaseNode):
    
    def __init__(self, number):
        super(StartGroup, self).__init__()
        self.number = number
        
    def __str__(self):
        return "("
        

class EndGroup(_BaseNode):
    
    def __init__(self, start_group):
        super(EndGroup, self).__init__()
        self.start_group = start_group
        
    def __str__(self):
        return ")"
    

class BaseSplit(_BaseNode):
    
    def __init__(self, lazy=False):
        super(BaseSplit, self).__init__()
        self.lazy = lazy
        self.__connected = False
        
    def concatenate(self, next):
        if next:
            if self.__connected:
                raise GraphException('Node already connected')
            if self.lazy:
                self.next.insert(0, next)
            else:
                self.next.append(next)
            self.__connected = True
        return self


class Split(BaseSplit):
    
    def __init__(self, label, lazy=False):
        super(Split, self).__init__(lazy=lazy)
        self.__label = label + ('?' if lazy else '')
        
    def __str__(self):
        return self.__label


class Match(_BaseNode):
    
    def __str__(self):
        return 'Match'


class _AlphabetLineNode(_AlphabetNode):

    def __init__(self, alphabet, multiline):
        super(_AlphabetLineNode, self).__init__(alphabet)
        self.multiline = multiline
    

class Dot(_AlphabetLineNode):
    
    def __str__(self):
        return '.'


class StartOfLine(_AlphabetLineNode):
    
    def __str__(self):
        return '^'
    
    
class EndOfLine(_AlphabetLineNode):
    
    def __str__(self):
        return '$'
    

class GroupReference(_BaseNode):
    
    def __init__(self, number):
        super(GroupReference, self).__init__()
        self.number = number
        
    def __str__(self):
        return '\\\\' + str(self.number)


class Lookahead(BaseSplit):
    
    def __init__(self, sense, forwards):
        super(Lookahead, self).__init__(lazy=True)
        self.sense = sense
        self.forwards = forwards
        
    def __str__(self):
        return '(?' + \
            ('' if self.forwards else '<') + \
            ('=' if self.sense else '!') + '...)'


class StatefulCount(BaseSplit):
    
    def __init__(self, begin, end, range):
        super(StatefulCount, self).__init__(lazy=True)
        self.begin = begin
        self.end = end if range else begin
    
    def __str__(self):
        text = '{' + str(self.begin)
        if self.end != self.begin:
            text += ','
            if self.end is not None:
                text += str(self.end)
        text += '}'
        return text 