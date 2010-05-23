
from bisect import bisect_left
from collections import deque

from rxpy.graph import String, Dot, _BaseNode


class Alphabet(object):
    
    def __init__(self, min, max):
        self.min = min
        self.max = max
        
    def code_to_char(self, code):
        '''
        Convert a code - an integer value between min and max, that maps the
        alphabet to a contiguous set of integers - to a character in the
        alphabet.
        '''
    
    def char_to_code(self, char):
        '''
        Convert a character in the alphabet to a code - an integer value 
        between min and max, that maps the alphabet to a contiguous set of 
        integers.
        '''
        
    def coerce(self, char):
        '''
        Force a character in str, unicode, or the alphabet itself, to be a
        member of the alphabet. 
        '''
        
    def join(self, *strings):
        '''
        Construct a word in the alphabet, given a list of words and/or 
        characters.
        '''
        
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
        self.__alphabet = alphabet
        self.__intervals = deque()
        for interval in intervals:
            self.append(interval)
        self.__index = None
        self.__str = None
        
    def append(self, interval):
        '''
        Add an interval to the existing intervals.
        
        This maintains self.__intervals in the normalized form described above.
        '''
        self.__index = None
        self.__str = None
        
        (a1, b1) = map(self.__alphabet.coerce, interval)
        if b1 < a1:
            (a1, b1) = (b1, a1)
        intervals = deque()
        done = False
        while self.__intervals:
            # pylint: disable-msg=E1103
            # (pylint fails to infer type)
            (a0, b0) = self.__intervals.popleft()
            if a0 <= a1:
                if b0 < a1 and b0 != self.__alphabet.before(a1):
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
                if b1 < a0 and b1 != self.__alphabet.before(a0):
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
        intervals.extend(self.__intervals) # slurp remaining
        self.__intervals = intervals
        
    def __len__(self):
        '''
        The number of intervals in the range.
        '''
        return len(self.__intervals)
    
    def __getitem__(self, index):
        return self.__intervals[index]
    
    def __iter__(self):
        return iter(self.__intervals)
    
    def __contains__(self, c):
        '''
        Does the value lie within the intervals?
        '''
        if self.__index is None:
            self.__index = [interval[1] for interval in self.__intervals]
        if self.__index:
            index = bisect_left(self.__index, c)
            if index < len(self.__intervals):
                (a, b) = self.__intervals[index]
                return a <= c <= b
        return False
    
    def __format_interval(self, interval):
        (a, b) = interval
        if a == b:
            return self.__alphabet.to_str(a)
        elif a == self.__alphabet.before(b):
            return self.__alphabet.to_str(a) + self.__alphabet.to_str(b)
        else:
            return self.__alphabet.to_str(a) + '-' + self.__alphabet.to_str(b)

    def __str__(self):
        if self.__str is None:
            self.__str = \
                '[' + ''.join(map(self.__format_interval, self.__intervals)) + ']'
        return self.__str

    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        # pylint: disable-msg=W0212
        # (test for same class)
        return isinstance(other, CharSet) and str(self) == str(other)

    def invert(self):
        if not self.__intervals:
            inverted = deque([(self.__alphabet.min, self.__alphabet.max)])
        else:
            inverted = deque()
            (a, last) = self.__intervals[0]
            if a != self.__alphabet.min:
                inverted.append(
                    (self.__alphabet.code_to_char(self.__alphabet.min), 
                     self.__alphabet.before(a)))
            for (a, b) in list(self.__intervals)[1:]:
                inverted.append(
                    (self.__alphabet.after(last), self.__alphabet.before(a)))
                last = b
            if last != self.__alphabet.max:
                inverted.append(
                    (self.__alphabet.after(last), 
                     self.__alphabet.code_to_char(self.__alphabet.max)))
        self.__intervals = inverted
        self.__index = None
        self.__str = None
    
    def simplify(self):
        from rxpy.parser import ParseException

        if len(self.__intervals) == 0:
            raise ParseException('Empty range')
        elif len(self.__intervals) == 1:
            if self.__intervals[0][0] == self.__intervals[0][1]:
                return String(self.__intervals[0][0], self.__alphabet)
            elif self.__intervals[0][0] == self.__alphabet.min and \
                    self.__intervals[0][1] == self.__alphabet.max:
                return Dot()
        return self
         
