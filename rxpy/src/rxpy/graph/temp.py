
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


from rxpy.graph.opcode import String
from rxpy.lib import _STRINGS


class Sequence(object):
    '''
    A temporary node, used only during construction, that contains a sequence 
    of nodes.  When the contents are first referenced any consecutive strings
    are concatenated.  The lazy triggering of this fits with the evaluation 
    of the regular expression "tree", so that lower nodes are frozen first,
    if needed.
    '''
    
    def __init__(self, nodes, state):
        self._nodes = nodes
        self._frozen = False
        self._state = state
    
    def concatenate(self, next):
        self.__freeze()
        for node in reversed(self._nodes):
            next = node.concatenate(next)
        return next

    def __freeze(self):
        if not self._frozen:
            old_nodes = list(self._nodes)
            def flatten():
                acc = None
                while old_nodes:
                    node = old_nodes.pop()
                    if isinstance(node, Sequence) and not node._frozen:
                        old_nodes.extend(node._nodes)
                    elif isinstance(node, String) and (self._state.flags & _STRINGS):
                        if acc:
                            acc.text = self._state.alphabet.join(node.text, acc.text)
                        else:
                            acc = node
                    else:
                        if acc:
                            yield acc
                            acc = None
                        yield node
                if acc:
                    yield acc
            self._nodes = list(flatten())
            self._nodes.reverse()
            self._frozen = True
            
    def __str__(self):
        return ''.join(map(str, self._nodes))
    
    def consumer(self, lenient):
        for node in self._nodes:
            if node.consumer(lenient):
                return True
        return lenient
    
    @property
    def start(self):
        if self._nodes:
            self.__freeze()
            return self._nodes[0].start
        else:
            return None
    
    def clone(self, cache=None):
        if cache is None:
            cache = {}
        return Sequence([node.clone(cache) for node in self._nodes],
                        self._state)
    
    def __bool__(self):
        return bool(self._nodes)
    
    def __nonzero__(self):
        return self.__bool__()
    
    
class Alternatives(object):
    '''
    A temporary node that does the wiring necessary to connect various
    alternatives together within the same Split().  The alternatives all 
    connect back at the exit of the node.
    '''
    
    def __init__(self, sequences, split):
        self.__sequences = sequences
        self.__split = split
        
    def consumer(self, lenient):
        all = True
        for sequence in self.__sequences:
            all = all and sequence.consumer(lenient)
        return all
    
    def concatenate(self, next):
        # be careful here to handle empty sequences correctly
        for sequence in self.__sequences:
            if sequence:
                self.__split.next.append(sequence.start)
                sequence.concatenate(next)
            else:
                self.__split.next.append(next.start)
        return self.__split
    
    def clone(self, cache=None):
        if cache is None:
            cache = {}
        return Alternatives([sequence.clone(cache) 
                             for sequence in self.__sequences],
                             self.__split.clone(cache))
        
    @property
    def start(self):
        return self.__split


class Merge(object):
    '''
    Another temporary node, supporting the merge of several different arcs.
    
    The last node given is the entry point when concatenated.
    '''
    
    def __init__(self, consumes, *nodes):
        self._nodes = nodes
        self.consumes = consumes

    def concatenate(self, next):
        last = None
        for node in self._nodes:
            last = node.concatenate(next.start)
        return last
    
    @property
    def start(self):
        return self._nodes[-1].start

    def consumer(self, lenient):
        if self.consumes is None:
            return lenient
        else:
            return self.consumes
    
    def __str__(self):
        return str(self.start)
    
    def clone(self, cache):
        if cache is None:
            cache = {}
        return Merge(self.consumes,
                     *(node.clone(cache) for node in self._nodes))
