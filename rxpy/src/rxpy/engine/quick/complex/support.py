
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


from rxpy.engine.support import Fail, Groups


class State(object):
    '''
    This is heavily optimized to (1) cache a valid hash and (2) avoid creating
    new objects (copy on write for slowly changing structures).
    '''
    
    def __init__(self, index, text, groups=None, loops=None, checks=None, 
                 last_number=None, hash=0):
        self.__index = index
        self.__text = text
        # map from index to (text, start, end) where text and end may be None
        # - copy on write
        self.__groups = groups if groups else {}
        # a list of (index, count) - copy on write
        self.__loops = loops if loops else []
        # (offset, set(index)) - copy on write
        self.__checks = checks if checks else (0, set())
        self.__last_number = last_number
        # this is updated in parallel with the above
        self.__hash = hash
        # number of characters to skip or -1 if matched
        # never cloned on non-zero
        self.__skip = 0
        
    def clone(self, index=None, prefix=None):
        hash = self.__hash
        if index is not None:
            hash = hash ^ self.__index ^ index
        else:
            index = self.index
        if prefix is None:
            prefix = self.__text
        # don't clone contents - they are copy on write
        return State(index, prefix, groups=self.__groups, 
                     loops=self.__loops, checks=self.__checks, hash=hash)
        
    def __eq__(self, other):
        # don't include checks - they are not needed
        return other.index == self.index and \
                other.__groups == self.__groups and \
                other.__loops == self.__loops
    
    def __hash__(self):
        return self.__hash
    
    def start_group(self, number, offset):
        # copy (for write)
        groups = dict(self.__groups)
        self.__groups = groups
        old_triple = groups.get(number, None)
        if old_triple is None:
            # add key to hash (shift to avoid clashes with index)
            self.__hash ^= number << 8
        else:
            (_text, start, end) = old_triple
            if start is not None: self.__hash ^= start << 16
            if end is not None: self.__hash ^= end << 24
        new_triple = (None, offset, None)
        # add new value to hash
        self.__hash ^= offset << 16
        # and store
        groups[number] = new_triple
        # allows chaining on creating a new state
        return self
        
    def end_group(self, number, offset):
        # copy (for write)
        groups = dict(self.__groups)
        self.__groups = groups
        # we know key is present, so can ignore that
        old_triple = groups[number]
        (_text, start, end) = old_triple
        # remove old value from hash
        if end is not None: self.__hash ^= end << 24
        new_triple = (self.__text[start:offset], start, offset)
        # add new value to hash
        self.__hash ^= offset << 24
        # and store
        groups[number] = new_triple
        if number != 0:
            self.__last_number = number
    
    def increment_loop(self, index, end):
        # copy on write
        loops = list(self.__loops)
        self.__loops = loops
        # if current loop, get and check
        if loops and loops[-1][0] == index:
            prev = loops.pop()
            # drop from hash (added back later on increment)
            self.__hash ^= prev
            (_index, count) = prev
            # increment
            count += 1
            if count > end:
                raise Fail
        else:
            # starting new loop
            count = 0
        next = (index, count)
        # add to loops and hash
        loops.append(next)
        self.__hash ^= next
    
    def drop_loop(self, index):
        # copy on write
        loops = list(self.__loops)
        self.__loops = loops
        # drop from loops and hash
        prev = loops.pop()
        self.__hash ^= prev

    def check(self, offset, index):
        if offset != self.__checks[0]:
            self.__checks = (offset, set([index]))
        elif index in  self.__checks[1]:
            raise Fail
        else:
            self.__checks = (offset, self.__checks[1].union([index]))

    @property
    def index(self):
        return self.__index
    
    def advance(self, index, text=None):
        self.__hash ^= index ^ self.__index
        self.__index = index
        if text is not None:
            self.__text = text
        return self

    def groups(self, group_state):
        return Groups(group_state, self.__text, self.__groups, None, 
                      self.__last_number)
        
    def group(self, number):
        return self.__groups.get(number, (None, None, None))[0]
    
    @property
    def skip(self):
        return self.__skip
    
    @skip.setter
    def skip(self, skip):
        self.__hash ^= self.__skip ^ skip
        self.__skip = skip
        