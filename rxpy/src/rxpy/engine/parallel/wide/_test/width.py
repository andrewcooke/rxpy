
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


from unittest import TestCase

from rxpy.engine.parallel.wide.engine import WideEngine
from rxpy.parser.pattern import parse_pattern


def engine(parse, text, search=False, ticks=None, maxwidth=None, 
           hash_state=False):
    engine = WideEngine(*parse, hash_state=hash_state)
    results = engine.run(text, search=search)
    if ticks:
        assert engine.ticks == ticks, engine.ticks
    if maxwidth:
        assert engine.maxwidth == maxwidth, engine.maxwidth
    return results

def parse(pattern, flags=0):
    return parse_pattern(pattern, WideEngine, flags=flags)


class WidthTest(TestCase):
    
    def test_basics(self):
        # width of 2 as carrying fallback match
        assert engine(parse('b*'), 1000 * 'b', ticks=3003, maxwidth=2)
        assert engine(parse('b*'), 1000 * 'b' + 'c', ticks=3003, maxwidth=2)
        # width of 1 when no match until end
        assert engine(parse('b*c'), 1000 * 'b' + 'c', ticks=3004, maxwidth=1)
        assert engine(parse('b*?c'), 1000 * 'b' + 'c', ticks=3004, maxwidth=1)
        assert engine(parse('ab*c'), 'a' + 1000 * 'b' + 'c', ticks=3005, maxwidth=1)
        assert engine(parse('ab*?c'), 'a' + 1000 * 'b' + 'c', ticks=3005, maxwidth=1)

    def test_hash_state(self):
        # equivalently, we can use hashing (which shortcuts on match)
        assert engine(parse('b*'), 1000 * 'b', ticks=3003, maxwidth=2, hash_state=True)
    
    def test_groups(self):
        assert engine(parse('(b)*'), 1000 * 'b', ticks=5004, maxwidth=2)
        assert engine(parse('(b)*'), 1000 * 'b' + 'c', ticks=5004, maxwidth=2)
        assert engine(parse('(b)*c'), 1000 * 'b' + 'c', ticks=5005, maxwidth=1)
        assert engine(parse('(b)*?c'), 1000 * 'b' + 'c', ticks=5005, maxwidth=1)
        assert engine(parse('a(b)*c'), 'a' + 1000 * 'b' + 'c', ticks=5006, maxwidth=1)
        assert engine(parse('a(b)*?c'), 'a' + 1000 * 'b' + 'c', ticks=5006, maxwidth=1)
        assert engine(parse('(b)*'), 1000 * 'b', ticks=5004, maxwidth=2, hash_state=True)

    def test_re_test(self):
        assert engine(parse('.*?cd'), 1000*'abc'+'de', ticks=10005, maxwidth=2)
        # this could be optimised as a character
        assert engine(parse('(a|b)*?c'), 1000*'ab'+'cd', ticks=14007, maxwidth=1)

    def test_search(self):
        bk = 1000 * 'b'
        result = engine(parse('b*'), bk, search=True)
        assert result
        assert result.group(0) == bk, result.group(0)
        
        assert engine(parse('b*'), bk, ticks=3003, maxwidth=2, search=True)
        assert engine(parse('b*'), bk, ticks=3003, maxwidth=2, hash_state=True, search=True)
        assert engine(parse('.*?b*'), bk, ticks=3005, maxwidth=2)

        assert engine(parse('b*'), bk + 'c', ticks=3003, maxwidth=2, search=True)
        assert engine(parse('b*c'), bk + 'c', ticks=1505505, maxwidth=1002, search=True)
        assert engine(parse('b*?c'), bk + 'c', ticks=1505505, maxwidth=1002, search=True)
        assert engine(parse('ab*c'), 'a' + bk + 'c', ticks=4007, maxwidth=2, search=True)
        assert engine(parse('ab*?c'), 'a' + bk + 'c', ticks=4007, maxwidth=2, search=True)

        assert engine(parse('b*c'), bk + 'c', ticks=1505505, maxwidth=1002, search=True)
        assert engine(parse('.*?b*c'), bk + 'c', ticks=1507507, maxwidth=1002)
