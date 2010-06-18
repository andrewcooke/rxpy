
from bisect import bisect_left
from collections import deque

from rxpy.lib import UnsupportedOperation, unimplemented, ParseException
from rxpy.parser.graph import String, Dot, _BaseNode


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
            raise ParseException('Default alphabet does not handle case')
        return (False, self.join(self.coerce(char)))
    
    def unescape(self, code):
        '''
        By default, assume escape codes map to character codes.
        '''
        return self.code_to_char(code)
        
        
class CharSet(_BaseNode):
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
    
    def __init__(self, intervals, alphabet=None):
        from rxpy.alphabet.unicode import Unicode
        super(CharSet, self).__init__()
        if alphabet is None:
            alphabet = Unicode()
        self.alphabet = alphabet
        self.intervals = deque()
        for interval in intervals:
            self.append(interval)
        self.__index = None
        self.__str = None
        
    def append(self, interval):
        '''
        Add an interval to the existing intervals.
        
        This maintains self.intervals in the normalized form described above.
        '''
        self.__index = None
        self.__str = None
        
        (a1, b1) = map(self.alphabet.coerce, interval)
        if b1 < a1:
            (a1, b1) = (b1, a1)
        intervals = deque()
        done = False
        while self.intervals:
            # pylint: disable-msg=E1103
            # (pylint fails to infer type)
            (a0, b0) = self.intervals.popleft()
            if a0 <= a1:
                if b0 < a1 and b0 != self.alphabet.before(a1):
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
                if b1 < a0 and b1 != self.alphabet.before(a0):
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
        
    def __len__(self):
        '''
        The number of intervals in the range.
        '''
        return len(self.intervals)
    
    def __getitem__(self, index):
        return self.intervals[index]
    
    def __iter__(self):
        return iter(self.intervals)
    
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
    
    def __format_interval(self, interval):
        (a, b) = interval
        if a == b:
            return self.alphabet.to_str(a)
        elif a == self.alphabet.before(b):
            return self.alphabet.to_str(a) + self.alphabet.to_str(b)
        else:
            return self.alphabet.to_str(a) + '-' + self.alphabet.to_str(b)

    def __str__(self):
        if self.__str is None:
            self.__str = \
                '[' + ''.join(map(self.__format_interval, self.intervals)) + ']'
        return self.__str

    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        # pylint: disable-msg=W0212
        # (test for same class)
        return isinstance(other, CharSet) and str(self) == str(other)

    def invert(self):
        if not self.intervals:
            inverted = deque([(self.alphabet.min, self.alphabet.max)])
        else:
            inverted = deque()
            (a, last) = self.intervals[0]
            if a != self.alphabet.min:
                inverted.append(
                    (self.alphabet.code_to_char(self.alphabet.min), 
                     self.alphabet.before(a)))
            for (a, b) in list(self.intervals)[1:]:
                inverted.append(
                    (self.alphabet.after(last), self.alphabet.before(a)))
                last = b
            if last != self.alphabet.max:
                inverted.append(
                    (self.alphabet.after(last), 
                     self.alphabet.code_to_char(self.alphabet.max)))
        self.intervals = inverted
        self.__index = None
        self.__str = None
    
    def simplify(self):
        if len(self.intervals) == 0:
            raise ParseException('Empty range')
        elif len(self.intervals) == 1:
            if self.intervals[0][0] == self.intervals[0][1]:
                return String(self.intervals[0][0])
            elif self.intervals[0][0] == self.alphabet.min and \
                    self.intervals[0][1] == self.alphabet.max:
                return Dot()
        return self
    
    def visit(self, visitor, state=None):
        return visitor.character(self.next, self, state)

