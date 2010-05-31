

from rxpy.parser.parser import parse, ParserState
from rxpy.direct.visitor import Visitor


(I, M, S, U, X, A, _S, _B, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _STATEFUL, _BACKTRACE_OR) = ParserState._FLAGS

_LEAD = '_lead'


def compile(pattern, flags=0):
    return RegexObject(pattern, flags)


class RegexObject(object):
    
    def __init__(self, pattern, flags=0):
        self.__pattern = pattern
        self.__alphabet = None
        self.__flags = flags
        self.__match = parse(self.__pattern, flags=self.__flags)
        self.__search = None

    @property
    def flags(self):
        return self.__flags
        
    @property
    def groups(self):
        return self.__match[0].group_count
    
    @property
    def groupindex(self):
        return self.__match[0].group_names
    
    @property
    def pattern(self):
        return self.__pattern
        
    def match(self, text, pos=0, endpos=None):
        if endpos is not None:
            text = text[0:endpos]
        visitor = Visitor.from_parse_results(self.__match, text, pos=pos)
        if visitor:
            return MatchObject(visitor.groups)
        else:
            return None
    
    def search(self, text, pos=0, endpos=None):
        '''
        Add, then drop, a leading .*?
        '''
        if not self.__search:
            # TODO - convert self.__match
            self.__search = parse('(?P<%s>.*?)' % _LEAD + self.__pattern, 
                                  flags=self.__flags)
        if endpos is not None:
            text = text[0:endpos]
        visitor = Visitor.from_parse_results(self.__search, text, pos=pos)
        if visitor:
            groups = visitor.groups
            lead = groups[_LEAD]
            del groups[_LEAD]
            begin = len(lead)
            (s, b, e) = groups[0]
            groups[0] = (s[begin:], b+begin, e)
            return MatchObject(groups)
        else:
            return None
        
    def finditer(self, text, pos=0, endpos=None):
        found = True
        while found:
            found = self.search(text, pos, endpos)
            if found:
                yield found
                offset = found.end()
                pos += offset if offset else 1 
        
    def splititer(self, text, pos=0, endpos=None):
        first = True
        endpos = len(text) if endpos is None else endpos
        for found in self.finditer(text, pos, endpos):
            if first and found.start() - pos:
                yield ''
            yield text[pos:found.start()]
            for group in found.groups():
                if group is not None:
                    yield group
            pos = found.end()
        if pos < endpos:
            yield text[pos:endpos]
            
    def split(self, text, pos=0, endpos=None):
        return list(self.splititer(text, pos, endpos))
    
    
class MatchObject(object):
    
    def __init__(self, groups):
        self.__groups = groups
        
    def group(self, *indices):
        if not indices:
            indices = [0]
        if len(indices) == 1:
            return self.__groups.group(indices[0])
        else:
            return tuple(map(lambda n: self.__groups.group(n), indices))
        
    def groups(self, default=None):
        tuple(self.__groups.group(index+1, default=default) 
              for index in len(self.__groups))
        
    def start(self, group=0):
        return self.__groups.start(group)

    def end(self, group=0):
        return self.__groups.end(group)
    
    def span(self, group=0):
        return (self.start(group), self.end(group))
    

def match(pattern, text, flags=0):
    return RegexObject(pattern, flags).match(text)


def search(pattern, text, flags=0):
    return RegexObject(pattern, flags).search(text)


def sub(pattern, replacement, text, count=0):
    count = count if count else -1
    if not isinstance(pattern, RegexObject):
        pattern = RegexObject(pattern)
    result = ''
    while text and count != 0:
        m = pattern.search(text)
        if m:
            result += text[0:m.start()] + replacement
            text = text[m.end() if m.end() else 1:]
            count -= 1
        else:
            break
    result += text
    return result
