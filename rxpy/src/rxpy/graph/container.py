
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

from operator import or_

from rxpy.graph.base import BaseNode, AutoClone
from rxpy.graph.opcode import Split, CheckPoint, NoMatch, Repeat
from rxpy.lib import unimplemented
from rxpy.parser.support import ParserState


class BaseCollection(AutoClone):
    
    def __init__(self, contents=None):
        super(BaseCollection, self).__init__(fixed=['contents', 'fixed'])
        if contents is None:
            contents = []
        for content in contents:
            self._check(content)
        self.contents = list(contents)
        
    def append(self, content):
        self._check(content)
        self.contents.append(content)

    @unimplemented
    def _check(self, content):
        pass
    
    @unimplemented
    def consumer(self, lenient):
        pass
    
    @unimplemented
    def join(self, final, state):
        pass
    
    def clone(self):
        clone = super(BaseCollection, self).clone()
        clone.contents = list(map(lambda x: x.clone(), self.contents))
        return clone
    
    def __bool__(self):
        return reduce(or_, map(bool, self.contents), False)
    
    def __nonzero__(self):
        return self.__bool__()
        

class Sequence(BaseCollection):
    
    def _check(self, content):
        assert isinstance(content, BaseNode) or isinstance(content, BaseCollection)
    
    def consumer(self, lenient):
        for node in self.contents:
            if node.consumer(lenient):
                return True
        return False
    
    def join(self, final, state):
        for content in reversed(self.contents):
            final = content.join(final, state)
        return final
    
    def pop(self):
        content = self.contents.pop()
        if not isinstance(content, Sequence):
            content = Sequence([content])
        return content
    
    
class LabelMixin(object):
    
    def __init__(self, contents=None, label=None, **kargs):
        super(LabelMixin, self).__init__(contents=contents, **kargs)
        self.label = label
    
    
class LazyMixin(object):
    
    def __init__(self, contents=None, lazy=False, **kargs):
        super(LazyMixin, self).__init__(contents=contents, **kargs)
        self.lazy = lazy
    
    
class Loop(LazyMixin, LabelMixin, Sequence):
    
    def __init__(self, contents, state=None, lazy=False, once=False, label=None):
        super(Loop, self).__init__(contents=contents, lazy=lazy, label=label)
        self.once = once
        if not self.consumer(False) and not (state.flags & ParserState._UNSAFE):
            self.append(CheckPoint())

    def join(self, final, state):
        split = Split(self.label, consumes=True)
        inner = super(Loop, self).join(split, state)
        next = [final, inner]
        if not self.lazy:
            next.reverse()
        split.next = next
        if self.once:
            return inner
        else:
            return split


class CountedLoop(LazyMixin, Sequence):
    
    def __init__(self, contents, begin, end, state=None, lazy=False):
        super(CountedLoop, self).__init__(contents=contents, lazy=lazy)
        self.begin = begin
        self.end = end
        if end is None and (
                not (self.consumer(False) or (state.flags & ParserState._UNSAFE))):
            self.append(CheckPoint())

    def join(self, final, state):
        count = Repeat(self.begin, self.end, self.lazy)
        inner = super(CountedLoop, self).join(count, state)
        count.next = [final, inner]
        return count


class Alternatives(LabelMixin, BaseCollection):
    
    def __init__(self, contents=None, label='...|...', split=Split):
        super(Alternatives, self).__init__(contents=contents, label=label)
        self.split = split
    
    def _check(self, content):
        assert isinstance(content, Sequence)
    
    def consumer(self, lenient):
        for sequence in self.contents:
            if not sequence.consumer(lenient):
                return False
        return True
    
    def join(self, final, state):
        if len(self.contents) == 0:
            return NoMatch().join(final, state)
        elif len(self.contents) == 1:
            return self.contents[0].join(final, state)
        else:
            split = self.split(self.label)
            split.next = list(map(lambda x: x.join(final, state), self.contents))
            return split
        
    def _assemble(self, final):
        pass
    
    
class Optional(LazyMixin, Alternatives):
    
    def join(self, final, state):
        self.contents.append(Sequence())
        if self.lazy:
            self.contents.reverse()
        return super(Optional, self).join(final, state)


