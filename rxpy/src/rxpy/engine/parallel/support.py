
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


from rxpy.engine.support import Loops, Groups


class State(object):
    '''
    State for a particular thread (offset in the text is common to all threads).
    '''
    
    def __init__(self, graph, groups=None, loops=None, checks=None,
                 **groups_kargs):
        self.__graph = graph
        self.__groups = groups if groups is not None else [None, None, groups_kargs]
        self.__loops = loops
        self.__checks = checks
        self.match_offset = None
        
    def clone(self, graph=None, groups=None):
        if groups is None:
            try:
                groups = self.__groups.clone()
            except AttributeError:
                groups = list(self.__groups)
        try:
            loops = self.__loops.clone()
        except AttributeError:
            loops = self.__loops
        checks = set(self.__checks) if self.__checks else None
        return State(self.__graph if graph is None else graph, 
                     groups=groups, loops=loops, checks=checks)
        
    def __eq__(self, other):
        '''
        Equality to avoid state duplication (only; minimal logic, use with care)
        '''
        if self.match_offset is not None and other.match_offset == self.match_offset:
            return True 
        return self.__graph is other.__graph and \
            (list == type(self.__groups) == type(other.__groups) or \
                self.__groups == other.__groups) and \
            self.__loops == other.__loops
            
    def __hash__(self):
        '''
        Hash to avoid state duplication (only; minimal logic)
        '''
        if self.match_offset is not None:
            return 0
        h = hash(self.__graph) ^ hash(self.__loops)
        if list != type(self.__groups):
            h ^= hash(self.__groups)
        return h
    
    def start_group(self, number, offset):
        if number == 0:
            try:
                self.__groups[0] = offset
                return self
            except TypeError:
                pass
        self.__expand_groups()
        self.__groups.start_group(number, offset)
        return self
        
    def end_group(self, number, offset):
        if number == 0:
            try:
                self.__groups[1] = offset
                return self
            except TypeError:
                pass
        self.__expand_groups()
        self.__groups.end_group(number, offset)
        return self
    
    def __expand_groups(self):
        if not isinstance(self.__groups, Groups):
            save = self.__groups
            self.__groups = Groups(**save[2])
            if save[0] is not None:
                self.__groups.start_group(0, save[0])
            if save[1] is not None:
                self.__groups.end_group(0, save[1])
    
    def increment(self, node):
        self.__expand_loops()
        return self.__loops.increment(node)
    
    def drop(self, node):
        self.__expand_loops()
        self.__loops.drop(node)
        return self
    
    def __expand_loops(self):
        if not self.__loops:
            self.__loops = Loops()
    
    def advance(self, index=0):
        self.__graph = self.__graph.next[index]
        return self
    
    def uncheck(self):
        self.__checks = None
        return self

    def check(self, check_point):
        if not self.__checks:
            self.__checks = set([check_point])
            return True
        else:
            if check_point in self.__checks:
                return False
            else:
                self.__checks.add(check_point)
                return True

    @property
    def graph(self):
        return self.__graph
    
    @property
    def groups(self):
        self.__expand_groups()
        return self.__groups


class States(object):
    
    def __init__(self, initial, hash_state):
        self._current_nodes = []
        self._next_nodes = initial
        self._hash_state = hash_state
        self.__matched = False
        self.__known = set() if hash_state else None

    def flip(self):
        '''
        Prepare for a new iteration.  Called before each iteration.
        '''
        self._current_nodes, self._next_nodes = self._next_nodes, []
        self._current_nodes.reverse()
        self.__matched = False
        self.__known = set()
        
    def pop(self):
        return self._current_nodes.pop()
        
    def add_extra(self, extra):
        if not self.__matched:
            self._current_nodes.extend(extra)
        
    def add_next(self, next):
        if next and not self.__matched and \
                (not self._hash_state or next not in self.__known):
            self._next_nodes.append(next.uncheck())
            self.__matched = next.match_offset is not None
            if self._hash_state:
                self.__known.add(next)
    
    def __bool__(self):
        '''
        Are there more current nodes (without flipping)?
        '''
        return bool(self._current_nodes) and not self.__matched
    
    def __non_zero__(self):
        return self.__bool__()
    
    def __len__(self):
        return len(self._current_nodes)

    @property
    def matched(self):
        '''
        Expose the __matched attribute, indicating if we have a matched state
        (in which case lower priority additions are pointless).
        '''
        return self.__matched
    
    @property
    def more(self):
        '''
        More states?  Called when __bool__ is False, before flip.
        '''
        return bool(self._next_nodes)
    
    @property
    def final_state(self):
        '''
        Return final state, if a match, or None. Called when __bool__ is False, 
        before flip.
        ''' 
        if self._next_nodes and self._next_nodes[0].match_offset is not None:
            return self._next_nodes[0]
        else:
            return None
