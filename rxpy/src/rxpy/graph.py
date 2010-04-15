

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
        

class BaseNode(object):
    
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
        

class AlphabetNode(BaseNode):
    
    def __init__(self, alphabet):
        super(AlphabetNode, self).__init__()
        self.alphabet = alphabet
    

class String(AlphabetNode):
    
    def __init__(self, text, alphabet):
        super(String, self).__init__(alphabet)
        self.text = text
        
    def __str__(self):
        return self.alphabet.to_str(self.text)


class StartGroup(BaseNode):
    
    def __init__(self, number):
        super(StartGroup, self).__init__()
        self.number = number
        
    def __str__(self):
        return "("
        

class EndGroup(BaseNode):
    
    def __init__(self, start_group):
        super(EndGroup, self).__init__()
        self.start_group = start_group
        
    def __str__(self):
        return ")"
    

class BaseSplit(BaseNode):
    
    def __init__(self, lazy=False):
        super(BaseSplit, self).__init__()
        self.__lazy = lazy
        self.__connected = False
        
    def concatenate(self, next):
        if next:
            if self.__connected:
                raise GraphException('Node already connected')
            if self.__lazy:
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


class Match(BaseNode):
    
    def __str__(self):
        return 'Match'


class Dot(AlphabetNode):
    
    def __str__(self):
        return '.'


class StartOfLine(AlphabetNode):
    
    def __str__(self):
        return '^'
    
    
class EndOfLine(AlphabetNode):
    
    def __str__(self):
        return '$'
    

class GroupReference(BaseNode):
    
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

