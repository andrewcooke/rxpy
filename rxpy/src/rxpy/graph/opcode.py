
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


from rxpy.graph.support import BaseNode, BaseSplitNode, BaseLineNode,\
    GraphException, BaseEscapedNode, CharSet


class String(BaseNode):
    '''
    Match a series of literal characters.
    '''
    
    def __init__(self, text):
        super(String, self).__init__()
        self.text = text
        
    def __str__(self):
        return self.text
    
    def visit(self, visitor, state=None):
        return visitor.string(self.next, self.text, state)


class StartGroup(BaseNode):
    '''
    Mark the start of a group (to be saved).
    '''
    
    def __init__(self, number):
        super(StartGroup, self).__init__()
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        return "("
        
    def visit(self, visitor, state=None):
        return visitor.start_group(self.next, self.number, state)


class EndGroup(BaseNode):
    '''
    Mark the end of a group (to be saved).
    '''
    
    def __init__(self, number):
        super(EndGroup, self).__init__()
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        return ")"
    
    def visit(self, visitor, state=None):
        return visitor.end_group(self.next, self.number, state)


class Split(BaseSplitNode):
    
    def __init__(self, label, lazy=False):
        super(Split, self).__init__(lazy=lazy)
        self.label = label + ('?' if lazy else '')
        
    def __str__(self):
        return self.label

    def visit(self, visitor, state=None):
        return visitor.split(self.next, state)


class Match(BaseNode):
    
    def __str__(self):
        return 'Match'

    def visit(self, visitor, state=None):
        return visitor.match(state)


class NoMatch(BaseNode):
    
    def __str__(self):
        return 'NoMatch'

    def visit(self, visitor, state=None):
        return visitor.no_match(state)


class Dot(BaseLineNode):
    
    def __init__(self, multiline):
        super(Dot, self).__init__(multiline, consumer=True)

    def __str__(self):
        return '.'

    def visit(self, visitor, state=None):
        return visitor.dot(self.next, self.multiline, state)


class StartOfLine(BaseLineNode):
    
    def __str__(self):
        return '^'
    
    def visit(self, visitor, state=None):
        return visitor.start_of_line(self.next, self.multiline, state)

    
class EndOfLine(BaseLineNode):
    
    def __str__(self):
        return '$'
    
    def visit(self, visitor, state=None):
        return visitor.end_of_line(self.next, self.multiline, state)


class GroupReference(BaseNode):
    
    def __init__(self, number):
        super(GroupReference, self).__init__()
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        return '\\' + str(self.number)

    def visit(self, visitor, state=None):
        return visitor.group_reference(self.next, self.number, state)


class Lookahead(BaseSplitNode):
    
    def __init__(self, equal, forwards):
        super(Lookahead, self).__init__(lazy=True)
        self.equal = equal
        self.forwards = forwards
        
    def __str__(self):
        return '(?' + \
            ('' if self.forwards else '<') + \
            ('=' if self.equal else '!') + '...)'

    def visit(self, visitor, state=None):
        return visitor.lookahead(self.next, self, self.equal, self.forwards, state)


class Repeat(BaseNode):
    
    def __init__(self, begin, end, lazy):
        '''
        If end is None the range is open.  Note that lazy here is a flag,
        it doesn't change how the children are ordered.
        '''
        super(Repeat, self).__init__()
        self.begin = begin
        self.end = end
        self.lazy = lazy
        self.__connected = False
    
    def concatenate(self, next):
        if next:
            if self.__connected:
                raise GraphException('Node already connected')
            self.next.insert(0, next.start)
            self.__connected = True
        return self

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
    
    def visit(self, visitor, state=None):
        return visitor.repeat(self.next, self, self.begin, self.end, self.lazy, 
                              state)
    
    
class Conditional(BaseSplitNode):
    '''
    If the group exists, the second child should be followed, otherwise the
    first.
    '''
    
    def __init__(self, number, lazy=True):
        super(Conditional, self).__init__(lazy=lazy)
        assert isinstance(number, int)
        self.number = number
        
    def __str__(self):
        text = '(?(' + str(self.number) + ')...'
        if len(self.next) == 3:
            text += '|...'
        text += ')'
        return text 
    
    def visit(self, visitor, state=None):
        return visitor.conditional(self.next, self.number, state)


class WordBoundary(BaseEscapedNode):
    
    def __init__(self, inverted=False):
        super(WordBoundary, self).__init__('b', inverted, consumer=False)

    def visit(self, visitor, state=None):
        return visitor.word_boundary(self.next, self.inverted, state)


class Digit(BaseEscapedNode):
    
    def __init__(self, inverted=False):
        super(Digit, self).__init__('d', inverted)

    def visit(self, visitor, state=None):
        return visitor.digit(self.next, self.inverted, state)


class Space(BaseEscapedNode):
    
    def __init__(self, inverted=False):
        super(Space, self).__init__('s', inverted)

    def visit(self, visitor, state=None):
        return visitor.space(self.next, self.inverted, state)


class Word(BaseEscapedNode):
    
    def __init__(self, inverted=False):
        super(Word, self).__init__('w', inverted)

    def visit(self, visitor, state=None):
        return visitor.word(self.next, self.inverted, state)


class Character(BaseNode):
    '''
    Combine a `CharSet` with character classes.
    '''
    
    def __init__(self, intervals, alphabet, classes=None, 
                 inverted=False, complete=False):
        super(Character, self).__init__()
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
    
        
