
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

from rxpy.engine._test.test_re import ReTests
from rxpy.engine.quick.simple.engine import SimpleEngine


class SimpleTest(ReTests, TestCase):
    
    def default_engine(self):
        return SimpleEngine

    def test_bug_418626(self):
        # bugs 418626 at al. -- Testing Greg Chapman's addition of op code
        # SRE_OP_MIN_REPEAT_ONE for eliminating recursion on simple uses of
        # pattern '*?' on a long string.
        self.assertEqual(self._re.match('.*?c', 10000*'ab'+'cd').end(0), 20001)
        self.assertEqual(self._re.match('.*?cd', 5000*'ab'+'c'+5000*'ab'+'cde').end(0),
                         20003)
        self.assertEqual(self._re.match('.*?cd', 20000*'abc'+'de').end(0), 60001)
        # non-simple '*?' still used to hit the recursion limit, before the
        # non-recursive scheme was implemented.
#        self.assertEqual(self._re.search('(a|b)*?c', 10000*'ab'+'cd').end(0), 20001)
        pass

    def test_symbolic_refs(self):
        pass
    
    def test_sub_template_numeric_escape(self):
        pass
    
    def test_special_escapes(self):
        pass
    
    def test_search_coverage(self):
        pass
    
    def test_scanner(self):
        pass

    def test_repeat_minmax(self):
        pass
    
    def test_re_split(self):
        pass
    
    def test_re_match(self):
        pass
    
    def test_re_groupref_exists(self):
        pass
    
    def test_re_groupref(self):
        pass
    
    def test_re_findall(self):
        pass
    
    def test_qualified_re_split(self):
        pass
    
    def test_not_literal(self):
        pass
    
    def test_non_consuming(self):
        pass
    
    def test_ignore_case(self):
        pass
    
    def test_groupdict(self):
        pass
    
    def test_getattr(self):
        pass
    
    def test_expand(self):
        pass
    
    def test_category(self):
        pass
    
    def test_bug_725149(self):
        pass
    
    def test_bug_725106(self):
        pass

    def test_bug_527371(self):
        pass
    
    def test_bug_449964(self):
        pass
    
    def test_bug_117612(self):
        pass
    
    def test_bug_114660(self):
        pass
    
    def test_bug_113254(self):
        pass
    
    def test_bigcharset(self):
        pass
    
    def test_basic_re_sub(self):
        pass
    
    def test_all(self):
        pass
    
    def test_bug_448951(self):
        pass
    
