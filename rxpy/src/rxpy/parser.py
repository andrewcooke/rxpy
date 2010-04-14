
from rxpy.alphabet.base import CharSet
from rxpy.alphabet.unicode import Unicode
from rxpy.graph import String, StartGroup, EndGroup, Split, BaseNode, Match, Dot,\
    StartOfLine, EndOfLine


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
    
    
class Alternatives(BaseNode):
    '''
    A temporary node, similar to Sequence, but supporting several alternatives.
    Construction includes the addition of `Split` and `Merge` instances.
    '''
    
    def __init__(self, sequences):
        self._sequences = sequences
        
    def concatenate(self, next):
        split = Split(str(self))
        split.next = list(map(lambda s: s.start, self._sequences))
        merge = Merge(*self._sequences)
        merge.concatenate(next)
        return split
    
    def __str__(self):
        return '|'.join(map(str, self._sequences))


class Merge(object):
    '''
    Another temporary node, supporting the merge of several different arcs.
    
    The last node given is the entry point when concatenated.
    '''
    
    def __init__(self, *nodes):
        self._nodes = nodes

    def concatenate(self, next):
        last = None
        for node in self._nodes:
            last = node.concatenate(next)
        return last
    
    
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
        
    def append_character(self, character, escaped=False):
        '''
        Accept the given character, returning a new builder.
        
        If escaped is true then the value is always treated as a literal.
        '''

class SequenceBuilder(StatefulBuilder):
    
    def __init__(self, state):
        super(SequenceBuilder, self).__init__(state)
        self._alternatives = []
        self._nodes = []
    
    def append_character(self, character, escaped=False):
        if not escaped and character == '\\':
            return SimpleEscapeBuilder(self._state, self)
        elif not escaped and character == '(':
            return GroupEscapeBuilder(self._state, self)
        elif not escaped and character == ')':
            raise ParseException('Unexpected )')
        elif not escaped and character == '[':
            return CharSetBuilder(self._state, self)
        elif not escaped and character == ']':
            raise ParseException('Unexpected ]')
        elif not escaped and character == '.':
            self._nodes.append(Dot(self._state.alphabet))
        elif not escaped and character == '^':
            self._nodes.append(StartOfLine(self._state.alphabet))
        elif not escaped and character == '$':
            self._nodes.append(EndOfLine(self._state.alphabet))
        elif not escaped and character == '|':
            self._start_new_alternative()
        elif not escaped and character in '+?*':
            return RepeatBuilder(self._state, self, self._nodes.pop(), character)
        else:
            self._nodes.append(String(character, self._state.alphabet))
        return self
    
    def _start_new_alternative(self):
        self._alternatives.append(self._nodes)
        self._nodes = []
        
    def build_dag(self):
        self._start_new_alternative()
        sequences = map(Sequence, self._alternatives)
        if len(sequences) > 1:
            return Alternatives(sequences)
        else:
            return sequences[0]

    def __bool__(self):
        return bool(self._nodes)
    
    
class RepeatBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence, latest, character):
        super(RepeatBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._latest = latest
        self._initial_character = character
    
    def append_character(self, character):
        
        lazy = character == '?'
        split = Split('(?:' + str(self._latest) + ')' + self._initial_character,
                      lazy)
        
        if self._initial_character == '+':
            # this (frozen) sequence protects "latest" from coallescing 
            seq = Sequence([self._latest, split])
            split.next = [seq.start]
            self._parent_sequence._nodes.append(seq)
        elif self._initial_character == '?':
            split.next = [self._latest.start]
            self._parent_sequence._nodes.append(Merge(self._latest, split))
        elif self._initial_character == '*':
            split.next = [self._latest.concatenate(split)]
            self._parent_sequence._nodes.append(split)
        else:
            raise ParseException('Bad initial character for RepeatBuilder')
        
        if lazy:
            return self._parent_sequence
        else:
            return self._parent_sequence.append_character(character)
        
        
class GroupEscapeBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(GroupEscapeBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._count = 0
        
    def append_character(self, character, escaped=False):
        self._count += 1
        if self._count == 1:
            if character == '?':
                return self
            else:
                builder = GroupBuilder(self._state, self._parent_sequence)
                return builder.append_character(character, escaped)
        else:
            if character == ':':
                return GroupBuilder(self._state, self._parent_sequence, 
                                    binding=False)
            else:
                raise ParseException('Unexpected qualifier after (? - ' 
                                     + character)


class GroupBuilder(SequenceBuilder):
    
    # This must subclass SequenceBuilder rather than contain an instance
    # because that may itself return child builders.
    
    def __init__(self, state, sequence, binding=True):
        super(GroupBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._start = \
            StartGroup(self._state.next_group_count()) if binding else None
 
    def append_character(self, character, escaped=False):
        if not escaped and character == ')':
            contents = super(GroupBuilder, self).build_dag()
            if self._start:
                contents = \
                    Sequence([self._start, contents, EndGroup(self._start)])
            self._parent_sequence._nodes.append(contents)
            return self._parent_sequence
        else:
            # this allows further child groups to be opened, etc
            return super(GroupBuilder, self).append_character(character, escaped)
        

class CharSetBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(CharSetBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._charset = CharSet([], alphabet=state.alphabet)
        self._invert = None
        self._queue = None
        self._range = False
    
    def append_character(self, character, escaped=False):
        
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
        elif not escaped and character == '\\':
            return SimpleEscapeBuilder(self._state, self)
        elif escaped or character not in "-]":
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
    

class SimpleEscapeBuilder(StatefulBuilder):
    
    LENGTH = {'x': 2, 'u': 4, 'U': 8}
    
    def __init__(self, state, builder):
        super(SimpleEscapeBuilder, self).__init__(state)
        self._parent_builder = builder
        self._buffer = ''
        self._remaining = 1
        
    def __exit(self):
        char = self._state.alphabet.unescape('\\' + self._buffer)
        return self._parent_builder.append_character(char, escaped=True)
        
    def append_character(self, character):
        if self._buffer:
            self._buffer += character
            self._remaining -= 1
            if not self._remaining:
                return self.__exit()
        else:
            self._buffer += character
            try:
                self._remaining = self.LENGTH[character]
            except KeyError:
                return self._parent_builder.append_character(character, escaped=True)
        return self
            
        
def parse(string):
    root = SequenceBuilder(ParserState())
    builder = root
    for character in string:
        builder = builder.append_character(character)
    if root != builder:
        raise ParseException('Incomplete expression')
    return builder.build_dag().concatenate(Match())
