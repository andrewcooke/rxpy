
from rxpy.alphabet.base import CharSet
from rxpy.alphabet.unicode import Unicode
from rxpy.graph import String, StartGroup, EndGroup, Split, BaseNode, Match


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
    
    def __init__(self, alphabet=None):
        self.__group_count = 0
        if alphabet is None:
            alphabet = Unicode()
        self.alphabet = alphabet
        
    def next_group_count(self):
        self.__group_count += 1
        return self.__group_count
    
    
class StatefulBuilder(object):
    
    def __init__(self, state):
        super(StatefulBuilder, self).__init__()
        self._state = state
        

class SequenceBuilder(StatefulBuilder):
    
    def __init__(self, state):
        super(SequenceBuilder, self).__init__(state)
        self._nodes = []
        self._escape = False
    
    def append_character(self, character):
        if not self._escape and character == '\\':
            self._escape = True
        elif not self._escape and character == '(':
            return GroupBuilder(self._state, self)
        elif not self._escape and character == ')':
            raise ParseException('Unexpected )')
        elif not self._escape and character == '[':
            return CharSetBuilder(self._state, self)
        elif not self._escape and character == ']':
            raise ParseException('Unexpected ]')
        elif not self._escape and character in '+?*':
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
        

class CharSetBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(CharSetBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._charset = CharSet([], alphabet=state.alphabet)
        self._invert = None
        self._escape = False
        self._queue = None
        self._range = False
    
    def append_character(self, character):
        
        def append():
            if self._range:
                if self._queue is None:
                    raise ParseException('Incomplete range')
                else:
                    self._charset.append((self._queue, character))
                    self._queue = None
                    self._range = False
            else:
                if self._queue:
                    self._charset.append((self._queue, self._queue))
                self._queue = character

        if self._invert is None and character == '^':
            self._invert = True 
        elif not self._escape and character == '\\':
            self._escape = True
        elif self._escape or character not in "-]":
            append()
        elif character == '-':
            if self._range:
                # repeated - is range to -?
                append()
            else:
                self._range = True
        elif character == ']':
            if self._queue:
                if self._range:
                    raise ParseException('Open range')
                else:
                    self._charset.append((self._queue, self._queue))
            if self._invert:
                self._charset.invert()
            self._parent_sequence._nodes.append(self._charset.simplify())
            return self._parent_sequence
        else:
            raise ParseException('Syntax error in character set')
        
        # after first character this must be known
        if self._invert is None:
            self._invert = False
            
        return self
        
def parse(string):
    root = SequenceBuilder(ParserState())
    builder = root
    for character in string:
        builder = builder.append_character(character)
    if root != builder:
        raise ParseException('Incomplete expression')
    return builder.build_dag().concatenate(Match())
