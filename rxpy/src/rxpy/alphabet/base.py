
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


from bisect import bisect_left
from collections import deque

from rxpy.lib import UnsupportedOperation, unimplemented, RxpyException
from rxpy.parser.graph import String, Dot, _BaseNode, NoMatch


class Alphabet(object):
    
    def __init__(self, min, max):
        self.min = min
        self.max = max
        
    @unimplemented
    def code_to_char(self, code):
        '''
        Convert a code - an integer value between min and max, that maps the
        alphabet to a contiguous set of integers - to a character in the
        alphabet.
        '''
    
    @unimplemented
    def char_to_code(self, char):
        '''
        Convert a character in the alphabet to a code - an integer value 
        between min and max, that maps the alphabet to a contiguous set of 
        integers.
        '''
        
    @unimplemented
    def coerce(self, char):
        '''
        Force a character in str, unicode, or the alphabet itself, to be a
        member of the alphabet. 
        '''
        
    @unimplemented
    def join(self, *strings):
        '''
        Construct a word in the alphabet, given a list of words and/or 
        characters.
        '''
        
    @unimplemented
    def to_str(self, char):
        '''
        Support display of the character.
        
        Note - this is the basis of hash and equality for intervals, so must
        be unique, repeatable, etc.
        '''
        
    def after(self, char):
        '''
        The character "before" the given one, or None
        '''
        code = self.char_to_code(char)
        if code < self.max:
            return self.code_to_char(code + 1)
        else:
            return None

    def before(self, char):
        '''
        The character "before" the given one, or None
        '''
        code = self.char_to_code(char)
        if code > self.min:
            return self.code_to_char(code - 1)
        else:
            return None
        
    def digit(self, char):
        '''
        Test whether the character is a digit or not.
        '''
        raise UnsupportedOperation('digit')
    
    def space(self, char):
        '''
        Test whether the character is a whitespace or not.
        '''
        raise UnsupportedOperation('space')
        
    def word(self, char):
        '''
        Test whether the character is a word character or not.
        '''
        raise UnsupportedOperation('word')
    
    def unpack(self, char, flags):
        '''
        Return either (True, CharSet) or (False, char)
        '''
        from rxpy.parser.parser import ParserState
        if flags & ParserState.IGNORECASE:
            raise RxpyException('Default alphabet does not handle case')
        return (False, self.join(self.coerce(char)))
    
    def unescape(self, code):
        '''
        By default, assume escape codes map to character codes.
        '''
        return self.code_to_char(code)
    
    
class CharSet(_BaseNode):
    '''
    Combine a `SimpleCharSet` with character classes.
    '''
    
    def __init__(self, intervals, alphabet, classes=None, 
                 inverted=False, complete=False):
        super(CharSet, self).__init__()
        self.__simple = SimpleCharSet(intervals, alphabet)
        self.alphabet = alphabet
        self.classes = classes if classes else []
        self.inverted = inverted
        self.complete = complete
        
    def _kargs(self):
        kargs = super(CharSet, self)._kargs()
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
    
        
class SimpleCharSet(object):
    '''
    A set of possible values for a character, described as a collection of 
    intervals.  Each interval is [a, b] (ie a <= x <= b, where x is a character 
    code).  We use open bounds to avoid having to specify an "out of range"
    value.
    
    The intervals are stored in a normalised list, ordered by a, joining 
    overlapping intervals as necessary.
    
    [This is based on lepl.regexp.interval.Character]
    '''
    
    # pylint: disable-msg=C0103 
    # (use (a,b) variables consistently)
    
    def __init__(self, intervals, alphabet):
        self.intervals = deque()
        self.__index = None
        self.__str = None
        for interval in intervals:
            self.append(interval, alphabet)
        
    def append(self, interval, alphabet):
        '''
        Add an interval to the existing intervals.
        
        This maintains self.intervals in the normalized form described above.
        '''
        self.__index = None
        self.__str = None
        
        (a1, b1) = map(alphabet.coerce, interval)
        if b1 < a1:
            (a1, b1) = (b1, a1)
        intervals = deque()
        done = False
        while self.intervals:
            # pylint: disable-msg=E1103
            # (pylint fails to infer type)
            (a0, b0) = self.intervals.popleft()
            if a0 <= a1:
                if b0 < a1 and b0 != alphabet.before(a1):
                    # old interval starts and ends before new interval
                    # so keep old interval and continue
                    intervals.append((a0, b0))
                elif b1 <= b0:
                    # old interval starts before and ends after new interval
                    # so keep old interval, discard new interval and slurp
                    intervals.append((a0, b0))
                    done = True
                    break
                else:
                    # old interval starts before new, but partially overlaps
                    # so discard old interval, extend new interval and continue
                    # (since it may overlap more intervals...)
                    (a1, b1) = (a0, b1)
            else:
                if b1 < a0 and b1 != alphabet.before(a0):
                    # new interval starts and ends before old, so add both
                    # and slurp
                    intervals.append((a1, b1))
                    intervals.append((a0, b0))
                    done = True
                    break
                elif b0 <= b1:
                    # new interval starts before and ends after old interval
                    # so discard old and continue (since it may overlap...)
                    pass
                else:
                    # new interval starts before old, but partially overlaps,
                    # add extended interval and slurp rest
                    intervals.append((a1, b0))
                    done = True
                    break
        if not done:
            intervals.append((a1, b1))
        intervals.extend(self.intervals) # slurp remaining
        self.intervals = intervals
        
    def __contains__(self, c):
        '''
        Does the value lie within the intervals?
        '''
        if self.__index is None:
            self.__index = [interval[1] for interval in self.intervals]
        if self.__index:
            index = bisect_left(self.__index, c)
            if index < len(self.intervals):
                (a, b) = self.intervals[index]
                return a <= c <= b
        return False
    
    def __format_interval(self, interval, alphabet):
        (a, b) = interval
        if a == b:
            return alphabet.to_str(a)
        elif a == alphabet.before(b):
            return alphabet.to_str(a) + alphabet.to_str(b)
        else:
            return alphabet.to_str(a) + '-' + alphabet.to_str(b)

    def to_str(self, alphabet):
        if self.__str is None:
            self.__str = ''.join(map(lambda x: self.__format_interval(x, alphabet), 
                                     self.intervals))
        return self.__str

    def simplify(self, alphabet, default):
        if len(self.intervals) == 1:
            if self.intervals[0][0] == self.intervals[0][1]:
                return String(self.intervals[0][0])
            elif self.intervals[0][0] == alphabet.min and \
                    self.intervals[0][1] == alphabet.max:
                return Dot(True)
        return default
    
    def __bool__(self):
        return bool(self.intervals)
    
    def __nonzero__(self):
        return self.__bool__()
    
