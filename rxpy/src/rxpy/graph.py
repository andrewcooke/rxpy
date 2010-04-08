

class GraphException(Exception):
    pass


def linear_iterator(node):
    while node:
        yield node
        node = node.next
        

def edge_iterator(node):
    stack = [node]
    visited = set()
    while stack:
        node = stack.pop()
        edge = (node, node.next)
        if edge not in visited:
            if node.next:
                stack.append(node.next)
            yield edge
            visited.add(edge)
        try:
            for other in node.others:
                edge = (node, other)
                if edge not in visited:
                    stack.append(other)
                    yield edge
                    visited.add(edge)
        except AttributeError:
            pass
        

class BaseNode(object):
    
    def __init__(self):
        self.next = None
        
    def __iter__(self):
        return linear_iterator(self)
    
    @property
    def start(self):
        return self
    
    def concatenate(self, next):
        if next:
            self.next = next.start
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
    

class String(BaseNode):
    
    def __init__(self, text):
        super(String, self).__init__()
        self.text = text
        
    def __str__(self):
        # todo escape
        return self.text


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
    

class Split(BaseNode):
    
    def __init__(self, label):
        super(Split, self).__init__()
        self.__label = label
        self.others = None
        
    def __str__(self):
        return self.__label


   