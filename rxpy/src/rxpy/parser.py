
from rxpy.graph import String, StartGroup, EndGroup, Split, BaseNode


class ParseException(Exception):
    pass


class Sequence(BaseNode):
    '''
    A temporary node, used only during construction, that contains a sequence 
    of nodes.  When the contents are first referenced any consecutive strings
    are concatenated.  The lazy triggering of this fits with the evaluation 
    of the regular expression "tree", so that lower nodes are frozen first,
    if needed.
    '''
    
    def __init__(self, nodes):
        self._nodes = nodes
        self._frozen = False
    
    def concatenate(self, next):
        self.__freeze()
        for node in reversed(self._nodes):
            next = node.concatenate(next)
        return next

    def __freeze(self):
        if not self._frozen:
            old_nodes = list(self._nodes)
            def flatten():
                acc = None
                while old_nodes:
                    node = old_nodes.pop()
                    if isinstance(node, Sequence) and not node._frozen:
                        old_nodes.extend(node._nodes)
                    elif isinstance(node, String):
                        if acc:
                            acc.text = node.text + acc.text
                        else:
                            acc = node
                    else:
                        if acc:
                            yield acc
                            acc = None
                        yield node
                if acc:
                    yield acc
            self._nodes = list(flatten())
            self._nodes.reverse()
            self._frozen = True
            
    def __str__(self):
        return ''.join(map(str, self._nodes))
    
    @property
    def start(self):
        if self._nodes:
            self.__freeze()
            return self._nodes[0].start
        return None


class Merge(object):
    '''
    Another temporary node, supporting the merge of several different arcs.
    '''
    
    def __init__(self, split, rest):
        self._split = split
        self._rest = rest

    def concatenate(self, next):
        for node in self._rest:
            node.concatenate(next)
        return self._split.concatenate(next)


class ParserState(object):
    
    def __init__(self):
        self.__group_count = 0
        
    def next_group_count(self):
        self.__group_count += 1
        return self.__group_count
    
    
class StatefulNode(object):
    
    def __init__(self, state):
        super(StatefulNode, self).__init__()
        self._state = state
        

class SequenceBuilder(StatefulNode):
    
    def __init__(self, state):
        super(SequenceBuilder, self).__init__(state)
        self._nodes = []
    
    def append_character(self, character):
        if character == '(':
            return GroupBuilder(self._state, self)
        elif character == ')':
            raise ParseException('Unexpected )')
        elif character in '+?*':
            latest = self._nodes.pop()
            split = Split('(?' + str(latest) + ')' + character)
            if character == '+':
                # this (frozen) sequence protects "latest" from coallescing 
                seq = Sequence([latest, split])
                split.others = [seq.start]
                self._nodes.append(seq)
            elif character == '?':
                split.others = [latest.start]
                self._nodes.append(Merge(split, [latest]))
            elif character == '*':
                split.others = [latest.concatenate(split)]
                self._nodes.append(split)
        else:
            self._nodes.append(String(character))
        return self
            
    def build_dag(self):
        return Sequence(self._nodes)

    def __bool__(self):
        return bool(self._nodes)


class GroupBuilder(SequenceBuilder):
    # This must subclass SequenceBuilder rather than contain an instance
    # because that may itself return child builders.
    
    def __init__(self, state, sequence):
        super(GroupBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._start = None 
 
    def append_character(self, character):
        
        if self._start is None:
            # is this a non-binding group?
            if character == '?':
                self._start = False
                return self
            else:
                self._start = StartGroup(self._state.next_group_count())
                self._nodes.append(self._start)
                
        if character == ')':
            if self._start:
                self._nodes.append(EndGroup(self._start))
            self._parent_sequence._nodes.append(self.build_dag())
            return self._parent_sequence
        else:
            # this allows further child groups to be opened
            return super(GroupBuilder, self).append_character(character)
        
        
def parse(string):
    root = SequenceBuilder(ParserState())
    builder = root
    for character in string:
        builder = builder.append_character(character)
    if root != builder:
        raise ParseException('Incomplete explression')
    return builder.build_dag().concatenate(None)
