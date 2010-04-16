
from rxpy.alphabet.base import CharSet
from rxpy.alphabet.unicode import Unicode
from rxpy.graph import String, StartGroup, EndGroup, Split, BaseNode, Match, \
    Dot, StartOfLine, EndOfLine, GroupReference, Lookahead, StatefulCount


class ParseException(Exception):
    pass


class ParserState(object):
    
    def __init__(self, alphabet=None, stateful=False):
        if alphabet is None:
            alphabet = Unicode()
        self.alphabet = alphabet
        self.stateful = stateful
        self.__group_count = 0
        self.__name_to_count = {}
        self.__count_to_name = {}
        
    def next_group_count(self, name=None):
        self.__group_count += 1
        if name:
            self.__name_to_count[name] = self.__group_count
            self.__count_to_name[self.__group_count] = name
        return self.__group_count
    
    def count_for_name(self, name):
        if name in self.__name_to_count:
            return self.__name_to_count[name]
        else:
            raise ParseException('Unknown name: ' + name)
        
        
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
    
    def clone(self, cache=None):
        if cache is None:
            cache = {}
        return Sequence([node.clone(cache) for node in self._nodes])
    
    
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
        return '...|...'
    
    def clone(self, cache=None):
        if cache is None:
            cache = {}
        return Alternatives([sequence.clone(cache) 
                             for sequence in self._sequences])


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
    
    
class Builder(object):
    
    def __init__(self):
        super(Builder, self).__init__()
    
    def append_character(self, character, escaped=False):
        '''
        Accept the given character, returning a new builder.  A value of
        None is passed at the end of the input, allowing cleanup.
        
        If escaped is true then the value is always treated as a literal.
        '''

    
class StatefulBuilder(Builder):
    
    def __init__(self, state):
        super(StatefulBuilder, self).__init__()
        self._state = state
        

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
        elif not escaped and character == '{':
            return CountBuilder(self._state, self)
        elif not escaped and character == '}':
            raise ParseException('Unexpected }')
        elif not escaped and character == '.':
            self._nodes.append(Dot(self._state.alphabet))
        elif not escaped and character == '^':
            self._nodes.append(StartOfLine(self._state.alphabet))
        elif not escaped and character == '$':
            self._nodes.append(EndOfLine(self._state.alphabet))
        elif not escaped and character == '|':
            self._start_new_alternative()
        elif character and (not escaped and character in '+?*'):
            return RepeatBuilder(self._state, self, self._nodes.pop(), character)
        elif character:
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
        
        if self._initial_character == '+':
            self.build_plus(self._parent_sequence, self._latest, lazy)
        elif self._initial_character == '?':
            self.build_optional(self._parent_sequence, self._latest, lazy)
        elif self._initial_character == '*':
            self.build_star(self._parent_sequence, self._latest, lazy)
        else:
            raise ParseException('Bad initial character for RepeatBuilder')
        
        if lazy:
            return self._parent_sequence
        else:
            return self._parent_sequence.append_character(character)
        
    @staticmethod
    def build_optional(parent_sequence, latest, lazy):
        split = Split('...?', lazy)
        split.next = [latest.start]
        parent_sequence._nodes.append(Merge(latest, split))
    
    @staticmethod
    def build_plus(parent_sequence, latest, lazy):
        split = Split('...+', lazy)
        # this (frozen) sequence protects "latest" from coallescing 
        seq = Sequence([latest, split])
        split.next = [seq.start]
        parent_sequence._nodes.append(seq)
        
    @staticmethod
    def build_star(parent_sequence, latest, lazy):
        split = Split('...*', lazy)
        split.next = [latest.concatenate(split)]
        parent_sequence._nodes.append(split)
        
        
        
class GroupEscapeBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(GroupEscapeBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._count = 0
        
    def append_character(self, character):
        self._count += 1
        if self._count == 1:
            if character == '?':
                return self
            else:
                builder = GroupBuilder(self._state, self._parent_sequence)
                return builder.append_character(character)
        else:
            if character == ':':
                return GroupBuilder(self._state, self._parent_sequence, 
                                    binding=False)
            elif character in 'aiLmsux':
                raise ParseException(
                    'Options must be read and removed by pre-processing')
            elif character == 'P':
                return NamedGroupBuilder(self._state, self._parent_sequence)
            elif character == '#':
                return CommentGroupBuilder(self._state, self._parent_sequence)
            elif character == '=':
                return LookaheadBuilder(
                            self._state, self._parent_sequence, True, True)
            elif character == '!':
                return LookaheadBuilder(
                            self._state, self._parent_sequence, False, True)
            elif character == '<':
                return LookbackBuilder(self._state, self._parent_sequence)
            else:
                raise ParseException(
                    'Unexpected qualifier after (? - ' + character)
                
                
class BaseGroupBuilder(SequenceBuilder):
    
    # This must subclass SequenceBuilder rather than contain an instance
    # because that may itself return child builders.
    
    def __init__(self, state, sequence):
        super(BaseGroupBuilder, self).__init__(state)
        self._parent_sequence = sequence
 
    def append_character(self, character, escaped=False):
        if not escaped and character == ')':
            return self._build_group()
        else:
            # this allows further child groups to be opened, etc
            return super(BaseGroupBuilder, self).append_character(character, escaped)
        
    def _build_group(self):
        pass
        

class GroupBuilder(BaseGroupBuilder):
    
    # This must subclass SequenceBuilder rather than contain an instance
    # because that may itself return child builders.
    
    def __init__(self, state, sequence, binding=True, name=None):
        super(GroupBuilder, self).__init__(state, sequence)
        self._start = \
            StartGroup(self._state.next_group_count(name)) if binding else None
 
    def _build_group(self):
        contents = self.build_dag()
        if self._start:
            contents = Sequence([self._start, contents, EndGroup(self._start)])
        self._parent_sequence._nodes.append(contents)
        return self._parent_sequence
        

class LookbackBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(LookbackBuilder, self).__init__(state)
        self._parent_sequence = sequence
        
    def append_character(self, character):
        if character == '=':
            return LookaheadBuilder(self._state, self._parent_sequence, True, False)
        elif character == '!':
            return LookaheadBuilder(self._state, self._parent_sequence, False, False)
        else:
            raise ParseException(
                'Unexpected qualifier after (?< - ' + character)
            

class LookaheadBuilder(BaseGroupBuilder):
    
    def __init__(self, state, sequence, sense, forwards):
        super(LookaheadBuilder, self).__init__(state, sequence)
        self._sense = sense
        self._forwards = forwards
        
    def _build_group(self):
        lookahead = Lookahead(self._sense, self._forwards)
        lookahead.next = [self.build_dag().concatenate(Match())]
        self._parent_sequence._nodes.append(lookahead)
        return self._parent_sequence
        

class NamedGroupBuilder(StatefulBuilder):
    '''
    Handle '(?P<name>pattern)' and '(?P=name)' by creating either creating a 
    matching group (and associating the name with the group number) or a
    group reference (for the group number).
    '''
    
    def __init__(self, state, sequence):
        super(NamedGroupBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._create = None
        self._name = ''
        
    def append_character(self, character, escaped=False):
        
        if self._create is None:
            if character == '<':
                self._create = True
            elif character == '=':
                self._create = False
            else:
                raise ParseException(
                    'Unexpected qualifier after (?P - ' + character)
                
        else:
            if self._create and not escaped and character == '>':
                if not self._name:
                    raise ParseException('Empty name for group')
                return GroupBuilder(self._state, self._parent_sequence, 
                                    True, self._name)
            elif not self._create and not escaped and character == ')':
                self._parent_sequence._nodes.append(
                    GroupReference(self._state.count_for_name(self._name)))
                return self._parent_sequence
            elif not escaped and character == '\\':
                return SimpleEscapeBuilder(self._state, self)
            elif character:
                self._name += character
            else:
                raise ParseException('Incomplete named group')

        return self
    
    
class CommentGroupBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(CommentGroupBuilder, self).__init__(state)
        self._parent_sequence = sequence
        
    def append_character(self, character, escaped=False):
        if not escaped and character == ')':
            return self._parent_sequence
        elif not escaped and character == '\\':
            return SimpleEscapeBuilder(self._state, self)
        elif character:
            return self
        else:
            raise ParseException('Incomplete comment')


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
        elif character and (escaped or character not in "-]"):
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
        if not character:
            raise ParseException('Incomplete character escape')
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
    

class CountBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(CountBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._begin = None
        self._end = None
        self._acc = ''
        self._range = False
        self._closed = False
        self._lazy = False
        
    def append_character(self, character):
        
        if self._closed:
            if not self._lazy and character == '?':
                self._lazy = True
                return self
            else:
                self.__build()
                return self._parent_sequence.append_character(character)
            
        if character == '}':
            self.__store_value()
            self._closed = True
        elif character == ',':
            self.__store_value()
        elif character:
            self._acc += character
        else:
            raise ParseException('Incomplete count specification')
        return self
            
    def __store_value(self):
        if self._begin is None:
            if not self._acc:
                raise ParseException('Missing lower limit for repeat')
            else:
                try:
                    self._begin = int(self._acc)
                except ValueError:
                    raise ParseException(
                            'Bad lower limit for repeat: ' + self._acc)
        else:
            if self._range:
                raise ParseException('Too many values in repeat')
            self._range = True
            if self._acc:
                try:
                    self._end = int(self._acc)
                except ValueError:
                    raise ParseException(
                            'Bad upper limit for repeat: ' + self._acc)
                if self._begin > self._end:
                    raise ParseException('Inconsistent repeat range')
        self._acc = ''
        
    def __build(self):
        if not self._parent_sequence._nodes:
            raise ParseException('Nothing to repeat')
        latest = self._parent_sequence._nodes.pop()
        if self._state.stateful:
            count = StatefulCount(self._begin, self._end, self._range)
            count.next = [latest.concatenate(count)]
            self._parent_sequence._nodes.append(count)
        else:
            for _i in range(self._begin):
                self._parent_sequence._nodes.append(latest.clone())
            if self._range:
                if self._end is None:
                    RepeatBuilder.build_star(
                            self._parent_sequence, latest.clone(), self._lazy)
                else:
                    for _i in range(self._end - self._begin):
                        RepeatBuilder.build_optional(
                                self._parent_sequence, latest.clone(), self._lazy)
                        
        
def parse(string, state=None):
    if not state:
        state = ParserState()
    root = SequenceBuilder(state)
    builder = root
    for character in string:
        builder = builder.append_character(character)
    builder = builder.append_character(None)
    if root != builder:
        raise ParseException('Incomplete expression')
    return root.build_dag().concatenate(Match())
