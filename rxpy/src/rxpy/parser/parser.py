
from string import digits

from rxpy.alphabet.base import CharSet
from rxpy.alphabet.unicode import Unicode
from rxpy.parser.graph import String, StartGroup, EndGroup, Split, _BaseNode, \
    Match, Dot, StartOfLine, EndOfLine, GroupReference, Lookahead, \
    Repeat, Conditional, WordBoundary, Word, Space, Digit


OCTAL = '01234567'


class ParseException(Exception):
    pass


class ParserState(object):
    
    def __init__(self, alphabet=None, stateful=False, multiline=False,
                 ascii=False):
        if alphabet is None:
            alphabet = Unicode()
        self.alphabet = alphabet
        self.stateful = stateful
        self.multiline = multiline
        self.ascii = ascii
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
        
    def count_for_name_or_count(self, name):
        try:
            return int(name)
        except:
            return self.count_for_name(name)
        
        
class Sequence(_BaseNode):
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
        else:
            return None
    
    def clone(self, cache=None):
        if cache is None:
            cache = {}
        return Sequence([node.clone(cache) for node in self._nodes])
    
    
class Alternatives(_BaseNode):
    '''
    A temporary node, similar to Sequence, but supporting several alternatives.
    Construction includes the addition of `Split` and `Merge` instances.
    '''
    
    def __init__(self, sequences, split=None):
        self._sequences = sequences
        self.__split = split
        
    def concatenate(self, next):
        if self.__split is None:
            self.__split = Split(str(self))
        self.__split.next = list(map(lambda s: s.start, self._sequences))
        merge = Merge(*self._sequences)
        merge.concatenate(next)
        return self.__split
    
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
    '''
    Base class for states in the parser (called Builder rather than State
    to avoid confusion with the parser state).
    
    The parser is a simple state machine, implemented via a separate loop
    (`parse()`) that repeatedly calls `.append_character()` on the current
    state, using whatever is returned as the next state.
    
    The graph is assembled within the states, which either assemble locally 
    or extend the state in a "parent" state (so states may reference parent
    states, but the evaluation process remains just a single level deep).
    
    It is also possible for one state to delegate to the append_character
    method of another state (escapes are handled in this way, for example).
    
    After all characters have been parsed, `None` is used as a final marker.
    '''
    
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
        if not escaped and character and character in ')]}':
            raise ParseException('Unexpected ' + character)
        elif not escaped and character == '\\':
            return ComplexEscapeBuilder(self._state, self)
        elif not escaped and character == '{':
            return CountBuilder(self._state, self)
        elif not escaped and character == '(':
            return GroupEscapeBuilder(self._state, self)
        elif not escaped and character == '[':
            return CharSetBuilder(self._state, self)
        elif not escaped and character == '.':
            self._nodes.append(Dot(self._state.multiline))
        elif not escaped and character == '^':
            self._nodes.append(StartOfLine(self._state.multiline))
        elif not escaped and character == '$':
            self._nodes.append(EndOfLine(self._state.multiline))
        elif not escaped and character == '|':
            self._start_new_alternative()
        elif character and (not escaped and character in '+?*'):
            return RepeatBuilder(self._state, self, self._nodes.pop(), character)
        elif character:
            self._nodes.append(String(character))
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
            elif character == '(':
                return ConditionalBuilder(self._state, self._parent_sequence)
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
    
    def __init__(self, state, sequence, binding=True, name=None):
        super(GroupBuilder, self).__init__(state, sequence)
        self._start = \
            StartGroup(self._state.next_group_count(name)) if binding else None
 
    def _build_group(self):
        contents = self.build_dag()
        if self._start:
            contents = Sequence([self._start, contents, 
                                 EndGroup(self._start.number)])
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
    '''
    If it's a reverse lookup we add an end of string matcher, and prefix ".*"
    so that we can use the matcher directly.
    '''
    
    def __init__(self, state, sequence, equal, forwards):
        super(LookaheadBuilder, self).__init__(state, sequence)
        self._equal = equal
        self._forwards = forwards
        if not self._forwards:
            RepeatBuilder.build_star(self, Dot(True), False)
        
    def _build_group(self):
        lookahead = Lookahead(self._equal, self._forwards)
        if not self._forwards:
            self._nodes.append(EndOfLine(False))
        lookahead.next = [self.build_dag().concatenate(Match())]
        self._parent_sequence._nodes.append(lookahead)
        return self._parent_sequence
        

class ConditionalBuilder(StatefulBuilder):
    '''
    Handle (?(id/name)yes-pattern|optional-no-pattern)
    '''
    
    def __init__(self, state, sequence):
        super(ConditionalBuilder, self).__init__(state)
        self.__parent_sequence = sequence
        self.__name = ''
        self.__yes = None
        
    def append_character(self, character, escaped=False):
        if not escaped and character == ')':
            return YesNoBuilder(self, self._state, self.__parent_sequence, '|)')
        elif not escaped and character == '\\':
            return SimpleEscapeBuilder(self._state, self)
        else:
            self.__name += character
            return self
        
    def callback(self, yesno, terminal):
        if self.__yes is None:
            (self.__yes, yesno) = (yesno, None)
            if terminal == '|':
                return YesNoBuilder(self, self._state, self.__parent_sequence, ')')
        group = self._state.count_for_name_or_count(self.__name)
        conditional = Conditional(group)
        yes = self.__yes.build_dag()
        yes = yes.start
        if yesno:
            no = yesno.build_dag()
            no = no.start
            alternatives = Alternatives([no, yes], conditional)
            self.__parent_sequence._nodes.append(alternatives)
        else:
            conditional.next = [yes]
            self.__parent_sequence._nodes.append(Merge(yes, conditional))
        return self.__parent_sequence
    
        
class YesNoBuilder(BaseGroupBuilder):
    
    def __init__(self, conditional, state, sequence, terminals):
        super(YesNoBuilder, self).__init__(state, sequence)
        self.__conditional = conditional
        self.__terminals = terminals
        
    def append_character(self, character, escaped=False):
        if character is None:
            raise ParseException('Incomplete conditional match')
        elif not escaped and character in self.__terminals:
            return self.__conditional.callback(self, character)
        else:
            return super(YesNoBuilder, self).append_character(character, escaped)


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
                # this is just for the name
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
        # not charset allows first character to be unescaped - or ]
        elif character and \
                ((not self._charset and not self._queue)
                 or escaped or character not in "-]"):
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
    '''
    Escaped characters only.
    '''
    
    def __init__(self, state, parent):
        super(SimpleEscapeBuilder, self).__init__(state)
        self._parent_builder = parent
        self.__std_escapes = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n',
                              'r': '\r', 't': '\t', 'v': '\v', '\\': '\\'}
        
    def append_character(self, character):
        if not character:
            raise ParseException('Incomplete character escape')
        elif character in 'xuU':
            return UnicodeEscapeBuilder(self._parent_builder, character)
        elif character in digits:
            return OctalEscapeBuilder(self._parent_builder, character)
        elif character in self.__std_escapes:
            return self._parent_builder.append_character(
                        self.__std_escapes[character], escaped=True)
        else:
            raise ParseException('Unexpected escape: ' + character)
    

class ComplexEscapeBuilder(SimpleEscapeBuilder):
    '''
    Extend SimpleEscapeBuilder to also handle group references.
    '''
    
    def __init__(self, state, parent):
        super(ComplexEscapeBuilder, self).__init__(state, parent)
        
    def append_character(self, character):
        if not character:
            raise ParseException('Incomplete character escape')
        elif character in digits and character != '0':
            return GroupReferenceBuilder(self._parent_builder, character)
        elif character == 'A':
            self._parent_builder._nodes.append(StartOfLine(False))
            return self._parent_builder
        elif character in 'bB':
            self._parent_builder._nodes.append(WordBoundary(character=='B'))
            return self._parent_builder
        elif character in 'dD':
            self._parent_builder._nodes.append(Digit(character=='D'))
            return self._parent_builder
        elif character in 'wW':
            self._parent_builder._nodes.append(Word(character=='W'))
            return self._parent_builder
        elif character in 'sS':
            self._parent_builder._nodes.append(Space(character=='S'))
            return self._parent_builder
        elif character == 'Z':
            self._parent_builder._nodes.append(EndOfLine(False))
            return self._parent_builder
        else:
            return super(ComplexEscapeBuilder, self).append_character(character)
        

class UnicodeEscapeBuilder(Builder):
    
    LENGTH = {'x': 2, 'u': 4, 'U': 8}
    
    def __init__(self, parent, initial):
        super(UnicodeEscapeBuilder, self).__init__()
        self.__parent_builder = parent
        self.__buffer = ''
        self.__remaining = self.LENGTH[initial]
        
    def append_character(self, character):
        if not character:
            raise ParseException('Incomplete unicode escape')
        self.__buffer += character
        self.__remaining -= 1
        if self.__remaining:
            return self
        try:
            return self.__parent_builder.append_character(
                        unichr(int(self.__buffer, 16)), escaped=True)
        except:
            raise ParseException('Bad unicode escape: ' + self.__buffer)
    

class OctalEscapeBuilder(Builder):
    
    def __init__(self, parent, initial=0):
        super(OctalEscapeBuilder, self).__init__()
        self.__parent_builder = parent
        self.__buffer = initial
        
    @staticmethod
    def decode(buffer):
        try:
            return unichr(int(buffer, 8))
        except:
            raise ParseException('Bad octal escape: ' + buffer)
        
    def append_character(self, character):
        if character and character in '01234567':
            self.__buffer += character
            if len(self.__buffer) == 3:
                return self.__parent_builder.append_character(
                            self.decode(self.__buffer), escaped=True)
            else:
                return self
        else:
            chain = self.__parent_builder.append_character(
                            self.decode(self.__buffer), escaped=True)
            return chain.append_character(character)
    

class GroupReferenceBuilder(Builder):
    
    def __init__(self, parent, initial):
        super(GroupReferenceBuilder, self).__init__()
        self.__parent_sequence = parent
        self.__buffer = initial
        
    def __octal(self):
        if len(self.__buffer) != 3:
            return False
        for c in self.__buffer:
            if c not in OCTAL:
                return False
        return True
    
    def __decode(self):
        try:
            return GroupReference(int(self.__buffer))
        except:
            raise ParseException('Bad group reference: ' + self.__buffer)
        
    def append_character(self, character):
        if character and character in digits:
            self.__buffer += character
            if self.__octal():
                return self.__parent_sequence.append_character(
                            OctalEscapeBuilder.decode(self.__buffer), 
                            escaped=True)
            else:
                return self
        else:
            self.__parent_sequence._nodes.append(self.__decode())
            return self.__parent_sequence.append_character(character)
    

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
            count = Repeat(self._begin, 
                           self._end if self._range else self._begin, 
                           self._lazy)
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
