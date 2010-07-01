
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
Support classes for parsing.
'''                               


from string import digits, ascii_letters

from rxpy.alphabet.ascii import Ascii
from rxpy.alphabet.unicode import Unicode
from rxpy.lib import _FLAGS, RxpyException, refuse_flags


OCTAL = '01234567'
ALPHANUMERIC = digits + ascii_letters


class ParserState(object):
    '''
    Encapsulate state needed by the parser.  This includes information 
    about flags (which may change during processing and is related to 
    alphabets) and groups.
    '''
    
    (I, M, S, U, X, A, _L, _S, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _LOOPS, _STRINGS) = _FLAGS
    
    def __init__(self, flags=0, alphabet=None, hint_alphabet=None,
                 require=0, refuse=0):
        '''
        `flags` - initial flags set by user (bits as int)
        
        `alphabet` - optional alphabet (if given, checked against flags; if not
        given inferred from flags and hint) 
        
        `hint_alphabet` - used to help auto-detect ASCII and Unicode in 2.6
        
        `require` - fkags required by the alphabet
        
        `refuse` - flags refused by the alphabet
        '''
        
        self.__new_flags = 0
        self.__initial_alphabet = alphabet
        self.__hint_alphabet = hint_alphabet
        self.__require = require
        self.__refuse = refuse
        
        flags = flags | require
        # default, if nothing specified, is unicode
        if alphabet is None and not (flags & (ParserState.ASCII | ParserState.UNICODE)):
            alphabet = hint_alphabet if hint_alphabet else Unicode()
        # else, if alphabet given, set flag
        elif alphabet:
            if isinstance(alphabet, Ascii): flags |= ParserState.ASCII
            elif isinstance(alphabet, Unicode): flags |= ParserState.UNICODE
            elif flags & (ParserState.ASCII | ParserState.UNICODE):
                raise RxpyException('The alphabet is inconsistent with the parser flags')
        # if alphabet missing, set from flag
        else:
            if flags & ParserState.ASCII: alphabet = Ascii()
            if flags & ParserState.UNICODE: alphabet = Unicode()
        # check contradictions
        if (flags & ParserState.ASCII) and (flags & ParserState.UNICODE):
            raise RxpyException('Cannot specify Unicode and ASCII together')
        refuse_flags(flags & refuse)
        
        
        self.__alphabet = alphabet
        self.__flags = flags
        self.__group_count = 0
        self.__name_to_index = {}
        self.__index_to_name = {}
        self.__comment = False  # used to track comments with extended syntax
        
    def deep_eq(self, other):
        '''
        Used only for testing.
        '''
        def eq(a, b):
            return a == b == None or (a and b and type(a) == type(b))
        return self.__new_flags == other.__new_flags and \
            eq(self.__initial_alphabet, other.__initial_alphabet) and \
            eq(self.__hint_alphabet, other.__hint_alphabet) and \
            self.__require == other.__require and \
            self.__refuse == other.__refuse and \
            eq(self.__alphabet, other.__alphabet) and \
            self.__flags == other.__flags and \
            self.__group_count == other.__group_count and \
            self.__name_to_index == other.__name_to_index and \
            self.__comment == other.__comment
        
    @property
    def has_new_flags(self):
        '''
        Have flags change during parsing (possible when flags are embedded in
        the regular expression)?
        '''
        return bool(self.__new_flags & ~self.__flags)
    
    def clone_with_new_flags(self):
        '''
        This discards group information because the expression will be parsed
        again with new flags.
        '''
        return ParserState(alphabet=self.__initial_alphabet, 
                           flags=self.__flags | self.__new_flags, 
                           hint_alphabet=self.__hint_alphabet,
                           require=self.__require, refuse=self.__refuse)
        
    def next_group_index(self, name=None):
        '''
        Get the index number for the next group, possibly associating it with
        a name.
        '''
        self.__group_count += 1
        if name:
            self.__name_to_index[name] = self.__group_count
            self.__index_to_name[self.__group_count] = name
        return self.__group_count
    
    def index_for_name(self, name):
        '''
        Given a group name, return the group index.
        '''
        if name in self.__name_to_index:
            return self.__name_to_index[name]
        else:
            raise RxpyException('Unknown name: ' + name)
        
    def index_for_name_or_count(self, name):
        '''
        Given a group name or index (as text), return the group index (as int).
        First, we parser as an integer, then we try as a name.
        '''
        try:
            return int(name)
        except:
            return self.index_for_name(name)
        
    def new_flag(self, flag):
        '''
        Add a new flag (called by the parser for embedded flags).
        '''
        self.__new_flags |= flag
        
    def significant(self, character):
        '''
        Returns false if character should be ignored (extended syntax). 
        '''
        if self.__flags & self.VERBOSE:
            if character == '#':
                self.__comment = True
                return False
            elif self.__comment:
                self.__comment = character != '\n'
                return False
            elif self.__alphabet.space(character):
                return False
            else:
                return True
        else:
            return True
        
    @property
    def alphabet(self):
        '''
        The alphabet to be used.
        '''
        return self.__alphabet
    
    @property
    def flags(self):
        '''
        Current flags (this does not change as new flags are added; instead
        the entire expression must be reparsed if `has_new_flags` is True.
        '''
        return self.__flags
    
    @property
    def group_names(self):
        '''
        Map from group names to index.
        '''
        return dict(self.__name_to_index)
    
    @property
    def group_indices(self):
        '''
        Map from group index to name.
        '''
        return dict(self.__index_to_name)
    
    @property
    def group_count(self):
        '''
        Total number of groups.
        '''
        return self.__group_count
        
        
class Builder(object):
    '''
    Base class for states in the parser (called Builder rather than State
    to avoid confusion with the parser state).
    
    The parser can be though of as a state machine, implemented via a separate 
    loop (`parse()`) that repeatedly calls `.append_character()` on the current
    state, using whatever is returned as the next state.
    
    The graph is assembled within the states, which either assemble locally 
    or extend the state in a "parent" state (so states may reference parent
    states, but the evaluation process remains just a single level deep).
    
    It is also possible for one state to delegate to the append_character
    method of another state (escapes are handled in this way, for example).
    
    After all characters have been parsed, `None` is used as a final character
    to flush any state that is waiting for lookahead.
    '''
    
    def __init__(self, state):
        super(Builder, self).__init__()
        self._state = state
    
    def append_character(self, character, escaped=False):
        '''
        Accept the given character, returning a new builder.  A value of
        None is passed at the end of the input, allowing cleanup.
        
        If escaped is true then the value is always treated as a literal.
        '''

        
def parse(text, state, class_, mutable_flags=True):
    '''
    Parse the text using the given builder.
    
    If the expression sets flags then it is parsed again.  If it changes flags
    on the second parse then an error is raised.
    '''
    graph = class_(state).parse(text)
    if mutable_flags and state.has_new_flags:
        state = state.clone_with_new_flags()
        graph = class_(state).parse(text)
    if state.has_new_flags:
        raise RxpyException('Inconsistent flags')
    return (state, graph)


