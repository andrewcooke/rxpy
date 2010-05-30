

from rxpy.parser.parser import parse, ParserState
from rxpy.direct.visitor import Visitor


(I, M, S, U, X, A, _S, _B, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _STATEFUL, _BACKTRACE_OR) = ParserState._FLAGS

_LEAD = '_lead'


def compile(pattern, flags=0):
    return Pattern(pattern, flags)


class Pattern(object):
    
    def __init__(self, pattern, flags=0):
        self.__pattern = pattern
        self.__alphabet = None
        self.__flags = flags
        self.__match = None
        self.__search = None
        
    def match(self, text, pos=0, endpos=None):
        if not self.__match:
            self.__match = parse(self.__pattern, flags=self.__flags)
        if endpos is not None:
            text = text[0:endpos]
        visitor = Visitor.from_parse_results(self.__match, text, pos=pos)
        return MatchObject(visitor.groups, 0, visitor.offset)
    
    def search(self, text, pos=0, endpos=None):
        '''
        Add, then drop, a leading .*?
        '''
        if not self.__search:
            self.__search = parse('(?P<%s>.*?)' % _LEAD + self.__pattern, 
                                  flags=self.__flags)
        if endpos is not None:
            text = text[0:endpos]
        visitor = Visitor.from_parse_results(self.__search, text, pos=pos)
        groups = visitor.groups
        lead = groups[_LEAD]
        del groups[_LEAD]
        begin = len(lead)
        groups[0] = groups[0][begin:]
        return MatchObject(groups, begin, visitor.offset)
    
    
class MatchObject(object):
    
    def __init__(self, groups, begin, end):
        self.__groups = groups
        self.begin = begin
        self.end = end
        
    def group(self, *indices):
        if not indices:
            indices = [0]
        if len(indices) == 1:
            return self.__groups[indices[0]]
        else:
            return tuple(map(lambda n: self.__groups[n], indices))

def match(pattern, text, flags=0):
    return Pattern(pattern, flags).match(text)


def search(pattern, text, flags=0):
    return Pattern(pattern, flags).search(text)


def sub(pattern, replacement, text, count=0):
    count = count if count else -1
    if not isinstance(pattern, Pattern):
        pattern = Pattern(pattern)
    result = ''
    while text and count != 0:
        m = pattern.search(text)
        result += text[0:m.begin] + replacement
        text = text[m.end:]
        count -= 1
    result += text
    return result
