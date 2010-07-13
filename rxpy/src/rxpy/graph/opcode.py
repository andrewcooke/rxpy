
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

'''
Nodes in this module are present in the final output from the parser.  They 
assume a context within the engine (a particular "current" position in the
input) and implicitly advance the position (if appropriate) on success.

See `BaseNode` for a general description of nodes.
'''

from rxpy.graph.base import BaseNode, BaseLineNode, BaseEscapedNode, \
    BaseGroupReference, BaseLabelledNode
from rxpy.graph.support import ReadsGroup, CharSet 

    
class String(BaseNode):
    '''
    Match a series of literal characters.
    
    - `text` will contain the characters (in the form appropriate for the
      alphabet)
    
    - `next` will contain a single value, which is the opcode to use if the
      match is successful. 
    '''
    
    def __init__(self, text):
        super(String, self).__init__(consumes=True, size=len(text))
        self.text = text
        
    def __str__(self):
        return self.text
    
    def extend(self, text, state):
        # TODO - use alphabet!
        self.text += text
        self.size = len(self.text)
    
    def visit(self, visitor, state=None):
        return visitor.string(self.next, self.text, state)


class StartGroup(BaseGroupReference):
    '''
    Mark the start of a group (to be saved).
    
    - `number` is the index for the group.

    - `next` will contain a single value, which is the following opcode.
    '''
    
    def __init__(self, number):
        assert isinstance(number, int)
        super(StartGroup, self).__init__(number, consumes=False, size=0)
        
    def __str__(self):
        return "(?P<%s>" % self.number
        
    def visit(self, visitor, state=None):
        return visitor.start_group(self.next, self.number, state)


class EndGroup(BaseGroupReference):
    '''
    Mark the end of a group (to be saved).
    
    - `number` is the index for the group.

    - `next` will contain a single value, which is the following opcode.
    '''
    
    def __init__(self, number):
        assert isinstance(number, int)
        super(EndGroup, self).__init__(number, consumes=False, size=0)
        
    def __str__(self):
        return ")"
    
    def visit(self, visitor, state=None):
        return visitor.end_group(self.next, self.number, state)


class Split(BaseLabelledNode):
    '''
    Branch the graph, providing alternative matches for the current context
    (eg via backtracking on failure).
    
    - `label` is a string for display (since this node represents many
      different parts of a regexp, like `|` and `*`).
    
    - `next` contains the alternatives, in ordered priority (`next[0]` first).  
      There should be more than 1, but only `|` should give more than 2. 
      However, the number of alternatives is not something the engine should 
      assume (I may be wrong, or there may be a "bug" that generates a single 
      entry in some cases, for example).
    '''
    
    def __init__(self, label, consumes=None):
        super(Split, self).__init__(label=label, consumes=consumes, 
                                    size=None if consumes is None else 0)
        self.fixed.remove('consumes') # set via constructor
        
    def visit(self, visitor, state=None):
        return visitor.split(self.next, state)

    def length(self, groups, known=None):
        if known is None:
            known = set()
        known.add(self)
        # avoid triggering loop detection via alternative different paths
        avoid_loops = set(known) 
        size = self.next[0].length(groups, known)
        if size is not None:
            for next in self.next[1:]:
                if size != next.length(groups, set(avoid_loops)):
                    return None
            return size
        else:
            return None
        

class Match(BaseNode):
    '''
    The terminal node.  If the engine "reaches" here then the match was a
    success.
    
    - `next` is undefined.
    '''
    
    def __init__(self):
        super(Match, self).__init__(consumes=False, size=0)
    
    def __str__(self):
        return 'Match'

    def visit(self, visitor, state=None):
        return visitor.match(state)
    
    def length(self, groups, known=None):
        return 0


class NoMatch(BaseNode):
    '''
    The current match has failed.  Currently this is generated when an attempt
    is made to match the complement of `.` (since `.` matches everything, the
    complement matches nothing). 
    
    TODO - remove the need for this by graph rewriting.
    
    - `next` is undefined.
    '''
    
    def __init__(self):
        super(NoMatch, self).__init__(consumes=False, size=0)
    
    def __str__(self):
        return 'NoMatch'

    def visit(self, visitor, state=None):
        return visitor.no_match(state)


class Dot(BaseLineNode):
    '''
    Match "any" single character.  The exact behaviour will depend on the
    alphabet and `multiline` (see the Python `re` documentation).
    
    - `multiline` indicates whether multiline mode is enabled (see the Python
      `re` documentation).
      
    - `next` will contain a single value, which is the opcode to use if the
      match is successful. 
    '''
    
    def __init__(self, multiline):
        super(Dot, self).__init__(multiline, consumes=True, size=1)

    def __str__(self):
        return '.'

    def visit(self, visitor, state=None):
        return visitor.dot(self.next, self.multiline, state)


class StartOfLine(BaseLineNode):
    '''
    Match the start of a line.  The exact behaviour will depend on the
    alphabet and `multiline` (see the Python `re` documentation).
    
    - `multiline` indicates whether multiline mode is enabled (see the Python
      `re` documentation).
      
    - `next` will contain a single value, which is the opcode to use if the
      match is successful. 
    '''
    
    def __init__(self, multiline):
        super(StartOfLine, self).__init__(multiline, consumes=False, size=0)
    
    def __str__(self):
        return '^'
    
    def visit(self, visitor, state=None):
        return visitor.start_of_line(self.next, self.multiline, state)

    
class EndOfLine(BaseLineNode):
    '''
    Match the end of a line.  The exact behaviour will depend on the
    alphabet and `multiline` (see the Python `re` documentation).
    
    - `multiline` indicates whether multiline mode is enabled (see the Python
      `re` documentation).
      
    - `next` will contain a single value, which is the opcode to use if the
      match is successful. 
    '''
    
    def __init__(self, multiline):
        super(EndOfLine, self).__init__(multiline, consumes=False, size=0)
    
    def __str__(self):
        return '$'
    
    def visit(self, visitor, state=None):
        return visitor.end_of_line(self.next, self.multiline, state)


class GroupReference(BaseGroupReference, ReadsGroup):
    '''
    Match the text previously matched by the given group.
    
    - `number` is the group index.
    
    - `next` will contain a single value, which is the opcode to use if the
      match is successful. 
    '''
    
    def __init__(self, number):
        super(GroupReference, self).__init__(number, consumes=None, size=None)
        
    def __str__(self):
        return '\\' + str(self.number)

    def visit(self, visitor, state=None):
        return visitor.group_reference(self.next, self.number, state)
    
    def length(self, groups, known=None):
        if known is None:
            known = set()
        if self not in known:
            known.add(self)
            if groups.data(self.number) is not None:
                return len(groups.group(self.number))


class Lookahead(BaseNode):
    '''
    Lookahead match (one that does not consume any input).
    
    - `equal` is `True` if the lookahead should succeed for the match to 
      continue and `False` if the lookahead should fail.
      
    - `forwards` is `True` if the lookahead should start from the current
      position and `False` if it should end there.
      
    - `next` contains two values.  `next[1]` is the lookahead expression;
      `next[0]` is the continuation of the normal match on success. 
      
    For lookbacks (`forwards` is `False`) the expression has a postfix of "$" 
    so that direct searching (not matching) of the string up to the current 
    point provides the to check.  Engines are welcome to use more efficient
    approaches, as long as the results remain correct.
    '''
    
    def __init__(self, equal, forwards):
        super(Lookahead, self).__init__(consumes=False, size=0)
        self.equal = equal
        self.forwards = forwards
        
    def __str__(self):
        return '(?' + \
            ('' if self.forwards else '<') + \
            ('=' if self.equal else '!') + '...)'

    def visit(self, visitor, state=None):
        return visitor.lookahead(self.next, self, self.equal, self.forwards, state)


class Repeat(BaseNode):
    '''
    A numerical repeat.
    
    - `begin` is the minimum count value.
    
    - `end` is the maximum count value (None for open ranges).
    
    - `lazy` indicates that matching should be lazy if `True`.
    
    - `next` contains two values.  `next[1]` is the expression to repeat
      (which loops back to here); `next[0]` is the continuation of the match 
      after repetition has finished.
    '''
    
    def __init__(self, begin, end, lazy):
        super(Repeat, self).__init__(consumes=None, size=None)
        self.begin = begin
        self.end = end
        self.lazy = lazy

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
    
    def length(self, groups, known=None):
        if known is None:
            known = set()
        if self.end == self.begin and self not in known:
            known.add(self)
            return self.begin * self.next[1].length(groups, known)
    
    def visit(self, visitor, state=None):
        return visitor.repeat(self.next, self, self.begin, self.end, self.lazy, 
                              state)
    
    
class GroupConditional(BaseLabelledNode, BaseGroupReference, ReadsGroup):
    '''
    Branch the graph, depending on the existence of a group.

    - `number` is the group index.
    
    - `label` is used to generate an informative graph plot.
    
    - `next` contains two nodes.  If the group exists, matching should continue
      with `next[1]`, otherwise with `next[0]`.
    '''
    
    def __init__(self, number, label):
        if str(number) not in label:
            label = '(?(' + str(number) + ')' + label + ')'
        super(GroupConditional, self).__init__(label=label,
                                               number=number, consumes=None)
        
    def length(self, groups, known=None):
        if known is None:
            known = set()
        if self not in known:
            known.add(self)
            if groups.data(self.number) is not None:
                return self.next[1].length(groups, known)
            else:
                return self.next[0].length(groups, known)
    
    def visit(self, visitor, state=None):
        return visitor.group_conditional(self.next, self.number, state)


class WordBoundary(BaseEscapedNode):
    '''
    Match a word boundary.  See Python `re` documentation and `BaseAlphabet.word`.
    
    - `inverted` indicates whether the test should succeed.  If `inverted` is
      `False` then the match should continue if the test succeeds; if `False`
      then the test should fail. 
    '''
    
    def __init__(self, inverted=False):
        super(WordBoundary, self).__init__('b', inverted, consumes=False, size=0)

    def visit(self, visitor, state=None):
        return visitor.word_boundary(self.next, self.inverted, state)


class Digit(BaseEscapedNode):
    '''
    Match a digit.  See `BaseAlphabet.digit`.
    
    - `inverted` indicates whether the test should succeed.  If `inverted` is
      `False` then the match should continue if the test succeeds; if `False`
      then the test should fail. 
    '''
    
    def __init__(self, inverted=False):
        super(Digit, self).__init__('d', inverted, consumes=True, size=1)

    def visit(self, visitor, state=None):
        return visitor.digit(self.next, self.inverted, state)


class Space(BaseEscapedNode):
    '''
    Match a space.  See `BaseAlphabet.space`.
    
    - `inverted` indicates whether the test should succeed.  If `inverted` is
      `False` then the match should continue if the test succeeds; if `False`
      then the test should fail. 
    '''
    
    def __init__(self, inverted=False):
        super(Space, self).__init__('s', inverted, consumes=True, size=1)

    def visit(self, visitor, state=None):
        return visitor.space(self.next, self.inverted, state)


class Word(BaseEscapedNode):
    '''
    Match a word character.  See `BaseAlphabet.word`.
    
    - `inverted` indicates whether the test should succeed.  If `inverted` is
      `False` then the match should continue if the test succeeds; if `False`
      then the test should fail. 
    '''
    
    def __init__(self, inverted=False):
        super(Word, self).__init__('w', inverted, consumes=True, size=1)

    def visit(self, visitor, state=None):
        return visitor.word(self.next, self.inverted, state)


class Character(BaseNode):
    '''
    Match a single character.  Currently the `__contains__` method should be
    used for testing; that will call the `BaseAlphabet` as required.
    
    How can this be improved?
    
    - `intervals` define simple character ranges (eg. 0-9).
    
    - `alphabet` is the alphabet used.
    
    - `classes` is a list of `(class_, label, invert)` triplets, where:
      - `class_` is a method on `alphabet` (eg. `.digit`)
      - `label` is used for display
      - `invert` is true if `class_` should fail
      
    - `inverted` is a global boolean that inverts the entire result (if `True`
      the test should fail).
      
    - `complete` is True if the test (without `invert`) will always succeed.   
    '''
    
    def __init__(self, intervals, alphabet, classes=None, 
                 inverted=False, complete=False):
        super(Character, self).__init__(consumes=True, size=1)
        self.__simple = CharSet(intervals, alphabet)
        self.alphabet = alphabet
        self.classes = classes if classes else []
        self.inverted = inverted
        self.complete = complete
        
    def _kargs(self):
        kargs = super(Character, self)._kargs()
        kargs['intervals'] = self.__simple.intervals
        return kargs
        
    def append_interval(self, interval):
        self.__simple.append(interval, self.alphabet)
        
    def append_class(self, class_, label, inverted=False):
        for (class2, _, inverted2) in self.classes:
            if class_ == class2:
                self.complete = self.complete or inverted != inverted2
                # if inverted matches, complete, else we already have it
                return
        self.classes.append((class_, label, inverted))
    
    def visit(self, visitor, state=None):
        return visitor.character(self.next, self, state)
    
    def invert(self):
        self.inverted = not self.inverted

    def __contains__(self, character):
        result = self.complete
        if not result:
            for (class_, _, invert) in self.classes:
                result = class_(character) != invert
                if result:
                    break
        if not result:
            result = character in self.__simple
        if self.inverted:
            result = not result
        return result
    
    def __str__(self):
        '''
        This returns (the illegal) [^] for all and [] for none.
        '''
        if self.complete:
            return '[]' if self.inverted else '[^]'
        contents = ''.join('\\' + label for (_, label, _) in self.classes)
        contents += self.__simple.to_str(self.alphabet)
        return '[' + ('^' if self.inverted else '') + contents + ']'
        
    def __hash__(self):
        return hash(str(self))
    
    def __bool__(self):
        return bool(self.classes or self.__simple)
    
    def __nonzero__(self):
        return self.__bool__()
    
    def simplify(self):
        if self.complete:
            if self.inverted:
                return NoMatch()
            else:
                return Dot(True)
        else:
            if self.classes or self.inverted:
                return self
            else:
                return self.__simple.simplify(self.alphabet, self)
    
        
class CheckPoint(BaseNode):
    '''
    Repetition of this point should include consumption of input.  This lets
    us detect and about infinite loops while using as little state and logic
    in the engine as possible.
    '''
    
    def __init__(self):
        # guarantees consumption of region
        super(CheckPoint, self).__init__(consumes=True, size=0)
        
    def visit(self, visitor, state=None):
        return visitor.check_point(self.next, self, state)

    def __str__(self):
        return '!'
