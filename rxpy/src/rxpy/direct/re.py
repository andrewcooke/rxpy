

from rxpy.parser.parser import parse, ParserState, ParseException
from rxpy.direct.visitor import Visitor, compile_repl
from string import ascii_letters, digits


(I, M, S, U, X, A, _S, _B, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _STATEFUL, _BACKTRACK_OR) = ParserState._FLAGS

_LEAD = '_lead'
_ALPHANUMERICS = ascii_letters + digits


def compile(pattern, flags=0):
    if isinstance(pattern, RegexObject):
        if flags:
            raise ValueError('Precompiled pattern')
    else:
        pattern = RegexObject(pattern, flags=flags)
    return pattern


class RegexObject(object):
    
    def __init__(self, pattern, flags=0):
        self.__pattern = pattern
        self.__flags = flags
        self.__parsed = parse(self.__pattern, flags=flags)
        self.__search = None
        
    @property
    def __state(self):
        return self.__parsed[0]

    @property
    def flags(self):
        return self.__flags
        
    @property
    def groups(self):
        return self.__state.group_count
    
    @property
    def groupindex(self):
        return self.__state.group_names
    
    @property
    def pattern(self):
        return self.__pattern
        
    def match(self, text, pos=0, endpos=None):
        return self.__match(text, pos=pos, endpos=endpos)
    
    def search(self, text, pos=0, endpos=None):
        return self.__match(text, pos=pos, endpos=endpos, search=True)
    
    def __match(self, text, pos=0, endpos=None, search=False):
        if endpos is not None:
            text = text[0:endpos]
        if pos <= len(text):
            visitor = Visitor.from_parse_results(self.__parsed, text, 
                                                 pos=pos, search=search)
            if visitor:
                return MatchObject(visitor.groups, self, text, pos, len(text),
                                   self.__state)
        return None
        
    def __searchiter(self, text, pos=0, endpos=None):
        found = True
        while found:
            found = self.search(text, pos, endpos)
            if found:
                yield found
                offset = found.end()
                pos = offset if offset > pos else offset + 1 

    def finditer(self, text, pos=0, endpos=None):
        pending_empty = None
        for found in self.__searchiter(text, pos=pos, endpos=endpos):
            # this is the "not touching" condition
            if pending_empty:
                if pending_empty.end() < found.start():
                    yield pending_empty
                pending_empty = None
            if found.group():
                yield found
            else:
                pending_empty = found
        if pending_empty:
            yield pending_empty

    def splititer(self, text, maxsplit=0):
        pos = 0
        maxsplit = maxsplit if maxsplit else -1
        for found in self.finditer(text):
            if found.group():
                yield text[pos:found.start()]
                for group in found.groups():
                    yield group
                pos = found.end()
                maxsplit -= 1
                if not maxsplit:
                    break
        yield text[pos:]
            
    def subn(self, repl, text, count=0):
        def subiter(count):
            # this implements the "not adjacent" condition
            count = count if count else -1
            prev = None
            pending_empty = None
            for found in self.__searchiter(text):
                if pending_empty:
                    if pending_empty.end() < found.start():
                        yield pending_empty
                        count -= 1
                        if not count:
                            break
                    pending_empty = None
                if found.group():
                    yield found
                    count -= 1
                    if not count:
                        break
                elif not prev or prev.end() < found.start():
                    pending_empty = found
                prev = found
            if pending_empty:
                yield pending_empty
        replacement = compile_repl(repl, self.__state)
        n = 0
        pos = 0
        results = []
        for found in subiter(count):
            results.append(text[pos:found.start()])
            results.append(replacement(found))
            n += 1
            pos = found.end()
        results += text[pos:]
        return (type(text)('').join(results), n)
    
    def findall(self, text, pos=0, endpos=None):
        def expand(match):
            if match.lastindex:
                groups = match.groups(default='')
                if len(groups) == 1:
                    return groups[0]
                else:
                    return groups
            else:
                return match.group()
        return list(map(expand, self.finditer(text, pos=pos, endpos=endpos)))
    
    def split(self, text, maxsplit=0):
        return list(self.splititer(text, maxsplit=maxsplit))
    
    def sub(self, repl, text, count=0):
        return self.subn(repl, text, count=count)[0]
    

class MatchObject(object):
    
    def __init__(self, groups, re, text, pos, endpos, state):
        self.__groups = groups
        self.re = re
        self.string = text
        self.pos = pos
        self.endpos = endpos
        self.__state = state
        self.lastindex = groups.lastindex
        self.lastgroup = groups.lastgroup
        
    def group(self, *indices):
        if not indices:
            indices = [0]
        if len(indices) == 1:
            return self.__groups.group(indices[0])
        else:
            return tuple(map(lambda n: self.__groups.group(n), indices))
        
    def groups(self, default=None):
        return tuple(self.__groups.group(index+1, default=default) 
                     for index in range(self.re.groups))
        
    def start(self, group=0):
        return self.__groups.start(group)

    def end(self, group=0):
        return self.__groups.end(group)
    
    def span(self, group=0):
        return (self.start(group), self.end(group))
    
    def groupdict(self, default=None):
        groups = {}
        for name in self.re.groupindex:
            groups[name] = self.__groups.group(name, default=default)
        return groups
    
    def expand(self, repl):
        replacement = compile_repl(repl, self.__state)
        return replacement(self)
        
    @property
    def regs(self):
        '''
        This is an undocumented hangover from regex in 1.5
        '''
        groups = [(self.start(index), self.end(index)) 
                    for index in range(self.re.groups+1)
                    if self.__groups.group(index)]
        return tuple(groups)
    
    
def match(pattern, text, flags=0):
    return compile(pattern, flags=flags).match(text)


def search(pattern, text, flags=0):
    return compile(pattern, flags=flags).search(text)


def findall(pattern, text, flags=0):
    return compile(pattern, flags=flags).findall(text)


def finditer(pattern, text, flags=0):
    return compile(pattern, flags=flags).finditer(text)


def sub(pattern, repl, text, count=0):
    return compile(pattern).sub(repl, text, count=count)


def subn(pattern, repl, text, count=0):
    return compile(pattern).subn(repl, text, count=count)


def split(pattern, text, maxsplit=0):
    return compile(pattern).split(text, maxsplit=maxsplit)


error = ParseException


def escape(text):
    def letters():
        for letter in text:
            if letter not in _ALPHANUMERICS:
                yield '\\'
            yield letter
    return type(text)('').join(list(letters()))
