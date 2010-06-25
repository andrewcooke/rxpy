
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


from string import digits, ascii_letters

from rxpy.lib import RxpyException
from rxpy.graph.opcode import Match, Character, String, Split, StartOfLine,\
    EndOfLine, Dot, StartGroup, EndGroup, Conditional, WordBoundary, Digit, Word,\
    Space, Lookahead, GroupReference, Repeat
from rxpy.graph.temp import Sequence, Alternatives, Merge
from rxpy.parser.support import StatefulBuilder, ParserState, OCTAL, parse


class SequenceBuilder(StatefulBuilder):
    
    def __init__(self, state):
        super(SequenceBuilder, self).__init__(state)
        self._alternatives = []
        self._nodes = []
        
    def parse(self, text):
        builder = self
        for character in text:
            builder = builder.append_character(character)
        builder = builder.append_character(None)
        if self != builder:
            raise RxpyException('Incomplete expression')
        return self.build_complete()
    
    def parse_group(self, text):
        '''
        Used to parse a set of groups for the Scanner.
        '''
        builder = GroupBuilder(self._state, self)
        if self._nodes:
            self.__start_new_alternative()
        for character in text:
            builder = builder.append_character(character)
        try:
            builder = builder.append_character(')')
            assert builder == self
        except:
            raise RxpyException('Incomplete group')
        
    def build_complete(self):
        return self.build_dag().concatenate(Match())
    
    def append_character(self, character, escaped=False):
        if not escaped and character == '\\':
            return ComplexEscapeBuilder(self._state, self)
        elif not escaped and character == '{':
            return CountBuilder(self._state, self)
        elif not escaped and character == '(':
            return GroupEscapeBuilder(self._state, self)
        elif not escaped and character == '[':
            return CharSetBuilder(self._state, self)
        elif not escaped and character == '.':
            self._nodes.append(Dot(self._state.flags & ParserState.DOTALL))
        elif not escaped and character == '^':
            self._nodes.append(StartOfLine(self._state.flags & ParserState.MULTILINE))
        elif not escaped and character == '$':
            self._nodes.append(EndOfLine(self._state.flags & ParserState.MULTILINE))
        elif not escaped and character == '|':
            self.__start_new_alternative()
        elif character and self._nodes and (not escaped and character in '+?*'):
            return RepeatBuilder(self._state, self, self._nodes.pop(), character)
        elif character and (escaped or self._state.significant(character)):
            (is_pair, value) = self._state.alphabet.unpack(character, 
                                                           self._state.flags)
            if is_pair:
                self._nodes.append(Character([(value[0], value[0]), 
                                             (value[1], value[1])], 
                                             self._state.alphabet))
            else:
                self._nodes.append(String(value))
        return self
    
    def __start_new_alternative(self):
        self._alternatives.append(self._nodes)
        self._nodes = []
        
    def build_dag(self):
        self.__start_new_alternative()
        sequences = map(lambda x: Sequence(x, self._state), self._alternatives)
        if len(sequences) > 1:
            return Alternatives(sequences, Split('...|...'))
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
        
        if character and character in '+*':
            raise RxpyException('Compound repeat: ' + 
                                 self._initial_character + character)
        elif self._initial_character == '?':
            self.build_optional(self._parent_sequence, self._latest, lazy)
        elif self._initial_character == '+':
            self.build_plus(self._parent_sequence, self._latest, lazy,
                            self._state)
        elif self._initial_character == '*':
            self.build_star(self._parent_sequence, self._latest, lazy)
        else:
            raise RxpyException('Bad initial character for RepeatBuilder')
            
        if lazy:
            return self._parent_sequence
        else:
            return self._parent_sequence.append_character(character)
        
    @staticmethod
    def assert_consumer(latest):
        if not latest.consumer:
            raise RxpyException('Cannot repeat ' + str(latest))
        
    @staticmethod
    def build_optional(parent_sequence, latest, lazy):
        split = Split('...?', lazy)
        split.next = [latest.start]
        parent_sequence._nodes.append(Merge(latest, split))
    
    @staticmethod
    def build_plus(parent_sequence, latest, lazy, state):
        RepeatBuilder.assert_consumer(latest)
        split = Split('...+', lazy)
        # this (frozen) sequence protects "latest" from coalescing 
        seq = Sequence([latest, split], state)
        split.next = [seq.start]
        parent_sequence._nodes.append(seq)
        
    @staticmethod
    def build_star(parent_sequence, latest, lazy):
        RepeatBuilder.assert_consumer(latest)
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
            elif character in ParserStateBuilder.INITIAL:
                return ParserStateBuilder(self._state, self._parent_sequence).append_character(character)
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
                raise RxpyException(
                    'Unexpected qualifier after (? - ' + character)
                
                
class ParserStateBuilder(StatefulBuilder):
    
    INITIAL = 'iLmsuxa_'
    
    def __init__(self, state, parent):
        super(ParserStateBuilder, self).__init__(state)
        self.__parent = parent
        self.__escape = False
        self.__table = {'i': ParserState.I,
                        'm': ParserState.M,
                        's': ParserState.S,
                        'u': ParserState.U,
                        'x': ParserState.X,
                        'a': ParserState.A,
                        '_s': ParserState._S,
                        '_g': ParserState._G}
        
    def append_character(self, character):
        if not self.__escape and character == '_':
            self.__escape = True
            return self
        elif self.__escape and character in 'sg':
            self._state.new_flag(self.__table['_' + character])
            self.__escape = False
            return self
        elif not self.__escape and character == 'L':
            raise RxpyException('Locale based classes unsupported')
        elif not self.__escape and character in self.__table:
            self._state.new_flag(self.__table[character])
            return self
        elif not self.__escape and character == ')':
            return self.__parent
        elif self.__escape:
            raise RxpyException('Unexpected characters after (? - _' + character)
        else:
            raise RxpyException('Unexpected character after (? - ' + character)
        

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
            StartGroup(self._state.next_group_index(name)) if binding else None
 
    def _build_group(self):
        contents = self.build_dag()
        if self._start:
            contents = Sequence([self._start, contents, EndGroup(self._start.number)],
                                 self._state)
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
            raise RxpyException(
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
        # first callback - have 'yes', possibly terminated by '|'
        if self.__yes is None:
            (self.__yes, yesno) = (yesno, None)
            # collect second alternative
            if terminal == '|':
                return YesNoBuilder(self, self._state, self.__parent_sequence, ')')
        group = self._state.index_for_name_or_count(self.__name)
        conditional = Conditional(group)
        yes = self.__yes.build_dag()
        no = yesno.build_dag() if yesno else None
        # Various possibilities here, depending on what is empty
        if yes:
            if no:
                alternatives = Alternatives([no, yes], conditional)
                self.__parent_sequence._nodes.append(alternatives)
            else:
                # Single alternative, which will be second child once connected
                # in graph (Conditional is lazy Split)
                conditional.next = [yes.start]
                self.__parent_sequence._nodes.append(Merge(yes, conditional))
        else:
            if no:
                conditional = Conditional(group, False)
                conditional.next = [no.start]
                self.__parent_sequence._nodes.append(Merge(no, conditional))
            else:
                # no point in doing anything at all!
                pass
        return self.__parent_sequence
    
        
class YesNoBuilder(BaseGroupBuilder):
    '''
    Collecy yes / no alternatives.
    '''
    
    def __init__(self, conditional, state, sequence, terminals):
        super(YesNoBuilder, self).__init__(state, sequence)
        self.__conditional = conditional
        self.__terminals = terminals
        
    def append_character(self, character, escaped=False):
        if character is None:
            raise RxpyException('Incomplete conditional match')
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
                raise RxpyException(
                    'Unexpected qualifier after (?P - ' + character)
                
        else:
            if self._create and not escaped and character == '>':
                if not self._name:
                    raise RxpyException('Empty name for group')
                return GroupBuilder(self._state, self._parent_sequence, 
                                    True, self._name)
            elif not self._create and not escaped and character == ')':
                self._parent_sequence._nodes.append(
                    GroupReference(self._state.index_for_name(self._name)))
                return self._parent_sequence
            elif not escaped and character == '\\':
                # this is just for the name
                return SimpleEscapeBuilder(self._state, self)
            elif character:
                self._name += character
            else:
                raise RxpyException('Incomplete named group')

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
            raise RxpyException('Incomplete comment')


class CharSetBuilder(StatefulBuilder):
    
    def __init__(self, state, sequence):
        super(CharSetBuilder, self).__init__(state)
        self._parent_sequence = sequence
        self._charset = Character([], alphabet=state.alphabet)
        self._invert = None
        self._queue = None
        self._range = False
    
    def append_character(self, character, escaped=False):
        
        def unpack(character):
            (is_charset, value) = self._state.alphabet.unpack(character, 
                                                              self._state.flags)
            if not is_charset:
                value = (character, character)
            return value
        
        def append(character=character):
            if self._range:
                if self._queue is None:
                    raise RxpyException('Incomplete range')
                else:
                    (alo, ahi) = unpack(self._queue)
                    (blo, bhi) = unpack(character)
                    self._charset.append_interval((alo, blo))
                    self._charset.append_interval((ahi, bhi))
                    self._queue = None
                    self._range = False
            else:
                if self._queue:
                    (lo, hi) = unpack(self._queue)
                    self._charset.append_interval((lo, lo))
                    self._charset.append_interval((hi, hi))
                self._queue = character

        if self._invert is None and character == '^':
            self._invert = True 
        elif not escaped and character == '\\':
            return SimpleEscapeBuilder(self._state, self)
        elif escaped and character in 'dD':
            self._charset.append_class(self._state.alphabet.digit,
                                       character, character=='D')
        elif escaped and character in 'wW':
            self._charset.append_class(self._state.alphabet.word,
                                       character, character=='W')
        elif escaped and character in 'sS':
            self._charset.append_class(self._state.alphabet.space,
                                       character, character=='S')
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
                    self._range = False
                    # convert open range to '-'
                    append('-')
                append(None)
            if self._invert:
                self._charset.invert()
            self._parent_sequence._nodes.append(self._charset.simplify())
            return self._parent_sequence
        else:
            raise RxpyException('Syntax error in character set')
        
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
                              'r': '\r', 't': '\t', 'v': '\v'}
        
    def append_character(self, character):
        if not character:
            raise RxpyException('Incomplete character escape')
        elif character in 'xuU':
            return UnicodeEscapeBuilder(self._state, self._parent_builder, character)
        elif character in digits:
            return OctalEscapeBuilder(self._state, self._parent_builder, character)
        elif character in self.__std_escapes:
            return self._parent_builder.append_character(
                        self.__std_escapes[character], escaped=True)
        elif character not in ascii_letters: # matches re.escape
            return self._parent_builder.append_character(character, escaped=True)
        else:
            return self._unexpected_character(character)
            
    def _unexpected_character(self, character):
        self._parent_builder.append_character(character, escaped=True)
        return self._parent_builder
    

class IntermediateEscapeBuilder(SimpleEscapeBuilder):
    '''
    Extend SimpleEscapeBuilder to also handle group references.
    '''
    
    def append_character(self, character):
        if not character:
            raise RxpyException('Incomplete character escape')
        elif character in digits and character != '0':
            return GroupReferenceBuilder(self._state, self._parent_builder, character)
        else:
            return super(IntermediateEscapeBuilder, self).append_character(character)
        
        
class ComplexEscapeBuilder(IntermediateEscapeBuilder):
    '''
    Extend IntermediateEscapeBuilder to handle character classes.
    '''
    
    def append_character(self, character):
        if not character:
            raise RxpyException('Incomplete character escape')
        elif character in digits and character != '0':
            return GroupReferenceBuilder(self._state, self._parent_builder, character)
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
        

class UnicodeEscapeBuilder(StatefulBuilder):
    
    LENGTH = {'x': 2, 'u': 4, 'U': 8}
    
    def __init__(self, state, parent, initial):
        super(UnicodeEscapeBuilder, self).__init__(state)
        self.__parent_builder = parent
        self.__buffer = ''
        self.__remaining = self.LENGTH[initial]
        
    def append_character(self, character):
        if not character:
            raise RxpyException('Incomplete unicode escape')
        self.__buffer += character
        self.__remaining -= 1
        if self.__remaining:
            return self
        try:
            return self.__parent_builder.append_character(
                    self._state.alphabet.code_to_char(int(self.__buffer, 16)), 
                    escaped=True)
        except:
            raise RxpyException('Bad unicode escape: ' + self.__buffer)
    

class OctalEscapeBuilder(StatefulBuilder):
    
    def __init__(self, state, parent, initial=0):
        super(OctalEscapeBuilder, self).__init__(state)
        self.__parent_builder = parent
        self.__buffer = initial
        
    @staticmethod
    def decode(buffer, alphabet):
        try:
            return alphabet.unescape(int(buffer, 8))
        except:
            raise RxpyException('Bad octal escape: ' + buffer)
        
    def append_character(self, character):
        if character and character in '01234567':
            self.__buffer += character
            if len(self.__buffer) == 3:
                return self.__parent_builder.append_character(
                            self.decode(self.__buffer, self._state.alphabet), 
                            escaped=True)
            else:
                return self
        else:
            chain = self.__parent_builder.append_character(
                            self.decode(self.__buffer, self._state.alphabet), 
                            escaped=True)
            return chain.append_character(character)
    

class GroupReferenceBuilder(StatefulBuilder):
    
    def __init__(self, state, parent, initial):
        super(GroupReferenceBuilder, self).__init__(state)
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
            index = int(self.__buffer)
            assert index <= self._state.group_count
            return GroupReference(index)
        except:
            raise RxpyException('Bad group reference: ' + self.__buffer)
        
    def append_character(self, character):
        if character and (
                (character in digits and len(self.__buffer) < 2) or 
                (character in OCTAL and len(self.__buffer) < 3)):
            self.__buffer += character
            if self.__octal():
                return self.__parent_sequence.append_character(
                            OctalEscapeBuilder.decode(self.__buffer, 
                                                      self._state.alphabet), 
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
        
        empty = not self._acc and self._begin is None
        if empty and character == '}':
            for character in '{}':
                self._parent_sequence.append_character(character, escaped=True)
            return self._parent_sequence
        elif character == '}':
            self.__store_value()
            self._closed = True
        elif character == ',':
            self.__store_value()
        elif character:
            self._acc += character
        else:
            raise RxpyException('Incomplete count specification')
        return self
            
    def __store_value(self):
        if self._begin is None:
            if not self._acc:
                raise RxpyException('Missing lower limit for repeat')
            else:
                try:
                    self._begin = int(self._acc)
                except ValueError:
                    raise RxpyException(
                            'Bad lower limit for repeat: ' + self._acc)
        else:
            if self._range:
                raise RxpyException('Too many values in repeat')
            self._range = True
            if self._acc:
                try:
                    self._end = int(self._acc)
                except ValueError:
                    raise RxpyException(
                            'Bad upper limit for repeat: ' + self._acc)
                if self._begin > self._end:
                    raise RxpyException('Inconsistent repeat range')
        self._acc = ''
        
    def __build(self):
        if not self._parent_sequence._nodes:
            raise RxpyException('Nothing to repeat')
        latest = self._parent_sequence._nodes.pop()
        if self._state.flags & ParserState._STATEFUL:
            self.build_count(self._parent_sequence, latest, self._begin, 
                             self._end if self._range else self._begin, 
                             self._lazy)
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
    
    @staticmethod
    def build_count(parent_sequence, latest, begin, end, lazy):
        '''
        If end is None, then range is open.
        '''
        count = Repeat(begin, end, lazy)
        count.next = [latest.concatenate(count)]
        parent_sequence._nodes.append(count)
                        
        
def parse_pattern(text, flags=0, alphabet=None, hint_alphabet=None):
    state = ParserState(flags=flags, alphabet=alphabet, 
                        hint_alphabet=hint_alphabet)
    return parse(text, state, SequenceBuilder)

def parse_groups(texts, flags=0, alphabet=None):
    state = ParserState(flags=flags, alphabet=alphabet)
    sequence = SequenceBuilder(state)
    for text in texts:
        sequence.parse_group(text)
    if state.has_new_flags:
        raise RxpyException('Inconsistent flags')
    return (state, sequence.build_complete())

