
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
Support classes shared by various engines.
'''                 

from operator import xor                   


class Fail(Exception):
    '''
    Raised on failure.
    '''
    pass


class Match(Exception):
    '''
    Raised on success
    '''
    pass


class Loops(object):
    '''
    The state needed to track explicit repeats (used in the `_LOOPS` flag
    was set).  This assumes that loops are nested (as they must be).
    '''
    
    def __init__(self, counts=None, order=None):
        # counts for loops in nested order
        self.__counts = counts if counts else []
        # map from node to position in counts list
        self.__order = order if order else {}
        
    def increment(self, node):
        if node not in self.__order:
            order = len(self.__counts)
            self.__order[node] = order
            self.__counts.append(0)
        else:
            order = self.__order[node]
            self.__counts = self.__counts[0:order+1]
            self.__counts[order] += 1
        return self.__counts[order]
    
    def drop(self, node):
        self.__counts = self.__counts[0:self.__order[node]]
        del self.__order[node]
        
    def clone(self):
        return Loops(list(self.__counts), dict(self.__order))
    
    def __eq__(self, other):
        return self.__counts == other.__counts and self.__order == other.__order
    
    def __hash__(self):
        return reduce(xor, map(hash, self.__counts) ^ \
                      reduce(xor, [hash(node) ^ hash(self.__order[node])
                                   for node in self.__order]))

class Groups(object):
    
    def __init__(self, text=None, groups=None, offsets=None, count=0, 
                 names=None, indices=None, lastindex=None):
        # text being matched
        self.__text = text
        # map from index to (text, start, end)
        self.__groups = groups if groups else {}
        # map from index to start for pending groups
        self.__offsets = offsets if offsets else {}
        # total number of groups declared in expression
        self.__count = count
        # map from group names to indices
        self.__names = names if names else {}
        # map from group indices to names
        self.__indices = indices if indices else {}
        # last index matched
        self.__lastindex = lastindex
        # cache for str
        self.__str = None
        
    def start_group(self, number, offset):
        self.__str = None
        self.__offsets[number] = offset
        
    def end_group(self, number, offset):
        assert isinstance(number, int)
        assert number in self.__offsets, 'Unopened group: ' + str(number) 
        self.__str = None
        self.__groups[number] = (self.__text[self.__offsets[number]:offset],
                                 self.__offsets[number], offset)
        del self.__offsets[number]
        if number: # avoid group 0
            self.__lastindex = number
    
    def __len__(self):
        return self.__count
    
    def __bool__(self):
        return bool(self.__groups)
    
    def __nonzero__(self):
        return self.__bool__()
    
    def __eq__(self, other):
        '''
        Ignores values from context (so does not work for comparison across 
        matches).
        '''
        return type(self) == type(other) and str(self) == str(other)
            
    def __hash__(self):
        '''
        Ignores values from context (so does not work for comparison across 
        matches).
        '''
        return hash(self.__str__())
    
    def __str__(self):
        '''
        Unique representation, used for eq and hash.  Ignores values from 
        context (so does not work for comparison across matches).
        '''
        if not self.__str:
            def fmt_group(index):
                group = self.__groups[index]
                return str(group[1]) + ':' + str(group[2]) + ':' + repr(group[0])
            self.__str = ';'.join(str(index) + '=' + fmt_group(index)
                            for index in sorted(self.__groups.keys())) + ' ' + \
                         ';'.join(str(index) + ':' + str(self.__offsets[index])
                            for index in sorted(self.__offsets.keys()))
        return self.__str
    
    def clone(self):
        return Groups(text=self.__text, groups=dict(self.__groups), 
                      offsets=dict(self.__offsets), count=self.__count, 
                      names=dict(self.__names), indices=dict(self.__indices),
                      lastindex=self.__lastindex)
    
    def data(self, number):
        if number in self.__names:
            index = self.__names[number]
        else:
            index = number
        try:
            return self.__groups[index]
        except KeyError:
            if isinstance(index, int) and index <= self.__count:
                return [None, -1, -1]
            else:
                raise IndexError(number)
            
    def group(self, number, default=None):
        group = self.data(number)[0]
        return default if group is None else group
        
    def start(self, number):
        return self.data(number)[1]
    
    def end(self, number):
        return self.data(number)[2]

    @property
    def lastindex(self):
        return self.__lastindex
    
    @property
    def lastgroup(self):
        return self.__indices.get(self.lastindex, None)
