
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


from rxpy.lib import RxpyException, _CHARS
from rxpy.graph._test.lib import GraphTest
from rxpy.parser.pattern import parse_pattern
from rxpy.parser.support import ParserState
from rxpy.engine.base import BaseEngine


class DummyEngine(BaseEngine):
    REQUIRE = _CHARS
    

def parse(pattern, engine=BaseEngine, flags=0):
    return parse_pattern(pattern, engine, flags=flags)


class ParserTest(GraphTest):
    
    def test_sequence(self):
        self.assert_graphs(parse('abc', engine=DummyEngine), 
"""digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="c"]
 3 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
}""")
        self.assert_graphs(parse('(?_c)abc'), 
"""digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="c"]
 3 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
}""")
        self.assert_graphs(parse('abc'), 
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")
    
    def test_matching_group(self):
        self.assert_graphs(parse('a(b)c'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="b"]
 3 [label=")"]
 4 [label="c"]
 5 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
}""")

    def test_nested_matching_group(self):
        self.assert_graphs(parse('a(b(c)d)e'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="b"]
 3 [label="(?P<2>"]
 4 [label="c"]
 5 [label=")"]
 6 [label="d"]
 7 [label=")"]
 8 [label="e"]
 9 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 7
 7 -> 8
 8 -> 9
}""")
        
    def test_nested_matching_close(self):
        self.assert_graphs(parse('a((b))c'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="(?P<2>"]
 3 [label="b"]
 4 [label=")"]
 5 [label=")"]
 6 [label="c"]
 7 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 7
}""")
        
    def test_matching_group_late_close(self):
        self.assert_graphs(parse('a(b)'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="b"]
 3 [label=")"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")

    def test_matching_group_early_open(self):
        self.assert_graphs(parse('(a)b'), 
"""digraph {
 0 [label="(?P<1>"]
 1 [label="a"]
 2 [label=")"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")

    def test_empty_matching_group(self):
        self.assert_graphs(parse('a()b'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label=")"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")
        self.assert_graphs(parse('()a'), 
"""digraph {
 0 [label="(?P<1>"]
 1 [label=")"]
 2 [label="a"]
 3 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
}""")
        
    def test_non_matching_group(self):
        self.assert_graphs(parse('a(?:b)c'),
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_non_matching_complex_group(self):
        self.assert_graphs(parse('a(?:p+q|r)c'), 
"""digraph {
 0 [label="a"]
 1 [label="...|..."]
 2 [label="p"]
 3 [label="r"]
 4 [label="c"]
 5 [label="Match"]
 6 [label="...+"]
 7 [label="q"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 5
 2 -> 6
 6 -> 2
 6 -> 7
 7 -> 4
}""")

    def test_character_plus(self):
        self.assert_graphs(parse('ab+c'), 
"""digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="...+"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 1
 2 -> 3
 3 -> 4
}""")

    def test_character_star(self):
        self.assert_graphs(parse('ab*c'), 
"""digraph {
 0 [label="a"]
 1 [label="...*"]
 2 [label="b"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 1
}""")
        
    def test_character_question(self):
        self.assert_graphs(parse('ab?c'), 
"""digraph {
 0 [label="a"]
 1 [label="...?"]
 2 [label="b"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 3
}""")
        # this was a bug
        self.assert_graphs(parse('x|a?'),
"""digraph {
 0 [label="...|..."]
 1 [label="x"]
 2 [label="...?"]
 3 [label="a"]
 4 [label="Match"]
 0 -> 1
 0 -> 2
 2 -> 3
 2 -> 4
 3 -> 4
 1 -> 4
}""")
        
    def test_multiple_character_question(self):
        self.assert_graphs(parse('ab?c?de?'), 
"""digraph {
 0 [label="a"]
 1 [label="...?"]
 2 [label="b"]
 3 [label="...?"]
 4 [label="c"]
 5 [label="d"]
 6 [label="...?"]
 7 [label="e"]
 8 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 3 -> 5
 5 -> 6
 6 -> 7
 6 -> 8
 7 -> 8
 4 -> 5
 2 -> 3
}""")
        
    def test_group_plus(self):
        self.assert_graphs(parse('a(bc)+d'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="bc"]
 3 [label=")"]
 4 [label="...+"]
 5 [label="d"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 1
 4 -> 5
 5 -> 6
}""")
        
    def test_group_star(self):
        self.assert_graphs(parse('a(bc)*d'), 
"""digraph {
 0 [label="a"]
 1 [label="...*"]
 2 [label="(?P<1>"]
 3 [label="d"]
 4 [label="Match"]
 5 [label="bc"]
 6 [label=")"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 5
 5 -> 6
 6 -> 1
}""")
        
    def test_group_question(self):
        self.assert_graphs(parse('a(bc)?d'), 
"""digraph {
 0 [label="a"]
 1 [label="...?"]
 2 [label="(?P<1>"]
 3 [label="d"]
 4 [label="Match"]
 5 [label="bc"]
 6 [label=")"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 5
 5 -> 6
 6 -> 3
}""")
        
    def test_simple_range(self):
        self.assert_graphs(parse('[a-z]'), 
"""digraph {
 0 [label="[a-z]"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_double_range(self):
        self.assert_graphs(parse('[a-c][p-q]'), 
"""digraph {
 0 [label="[a-c]"]
 1 [label="[pq]"]
 2 [label="Match"]
 0 -> 1
 1 -> 2
}""")    

    def test_single_range(self):
        self.assert_graphs(parse('[a]'), 
"""digraph {
 0 [label="a"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_autoescaped_range(self):
        self.assert_graphs(parse('[]]'), 
"""digraph {
 0 [label="]"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_inverted_range(self):
        self.assert_graphs(parse('[^apz]'), 
r"""digraph {
 0 [label="[^apz]"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_escaped_range(self):
        self.assert_graphs(parse(r'[\x00-`b-oq-y{-\U0010ffff]'), 
r"""digraph {
 0 [label="[\\x00-`b-oq-y{-\\U0010ffff]"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_x_escape(self):
        self.assert_graphs(parse('a\\x62c'), 
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_u_escape(self):
        self.assert_graphs(parse('a\\u0062c'), 
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_U_escape(self):
        self.assert_graphs(parse('a\\U00000062c'), 
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_escaped_escape(self):
        self.assert_graphs(parse('\\\\'), 
# unsure about this...
"""digraph {
 0 [label="\\\\"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_dot(self):
        self.assert_graphs(parse('.'), 
"""digraph {
 0 [label="."]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_lazy_character_plus(self):
        self.assert_graphs(parse('ab+?c'), 
"""digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="...+?"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 2 -> 1
 3 -> 4
}""")


    def test_lazy_character_star(self):
        self.assert_graphs(parse('ab*?c'), 
"""digraph {
 0 [label="a"]
 1 [label="...*?"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_lazy_character_question(self):
        self.assert_graphs(parse('ab??c'), 
"""digraph {
 0 [label="a"]
 1 [label="...??"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 2
 2 -> 4
}""")
        
    def test_lazy_group_plus(self):
        self.assert_graphs(parse('a(bc)+?d'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="bc"]
 3 [label=")"]
 4 [label="...+?"]
 5 [label="d"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 4 -> 1
 5 -> 6
}""")
        
    def test_lazy_group_star(self):
        self.assert_graphs(parse('a(bc)*?d'), 
"""digraph {
 0 [label="a"]
 1 [label="...*?"]
 2 [label="d"]
 3 [label="(?P<1>"]
 4 [label="bc"]
 5 [label=")"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 5
 5 -> 1
 2 -> 6
}""")
        
    def test_alternatives(self):
        self.assert_graphs(parse('a|'), 
"""digraph {
 0 [label="...|..."]
 1 [label="a"]
 2 [label="Match"]
 0 -> 1
 0 -> 2
 1 -> 2
}""")
        self.assert_graphs(parse('a|b|cd'), 
"""digraph {
 0 [label="...|..."]
 1 [label="a"]
 2 [label="b"]
 3 [label="cd"]
 4 [label="Match"]
 0 -> 1
 0 -> 2
 0 -> 3
 3 -> 4
 2 -> 4
 1 -> 4
}""")

    def test_group_alternatives(self):
        self.assert_graphs(parse('(a|b|cd)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="...|..."]
 2 [label="a"]
 3 [label="b"]
 4 [label="cd"]
 5 [label=")"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 1 -> 4
 4 -> 5
 5 -> 6
 3 -> 5
 2 -> 5
}""")
        self.assert_graphs(parse('(a|)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="...|..."]
 2 [label="a"]
 3 [label=")"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 3
}""")
        
    def test_nested_groups(self):
        self.assert_graphs(parse('a|(b|cd)'),
"""digraph {
 0 [label="...|..."]
 1 [label="a"]
 2 [label="(?P<1>"]
 3 [label="...|..."]
 4 [label="b"]
 5 [label="cd"]
 6 [label=")"]
 7 [label="Match"]
 0 -> 1
 0 -> 2
 2 -> 3
 3 -> 4
 3 -> 5
 5 -> 6
 6 -> 7
 4 -> 6
 1 -> 7
}""")

    def test_named_groups(self):
        self.assert_graphs(parse('a(?P<foo>b)c(?P=foo)d'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="b"]
 3 [label=")"]
 4 [label="c"]
 5 [label="\\\\1"]
 6 [label="d"]
 7 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 7
}""")
        
#    def test_comment(self):
#        self.assert_graphs(parse('a(?#hello world)b'), 
#"""digraph {
# 0 [label="ab"]
# 1 [label="Match"]
# 0 -> 1
#}""")
        
    def test_lookahead(self):
        self.assert_graphs(parse('a(?=b+)c'),
"""digraph {
 0 [label="a"]
 1 [label="(?=...)"]
 2 [label="c"]
 3 [label="b"]
 4 [label="...+"]
 5 [label="Match"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 3
 4 -> 5
 2 -> 6
}""")
        
    def test_lookback(self):
        self.assert_graphs(parse('a(?<=b+)c'),
"""digraph {
 0 [label="a"]
 1 [label="(?<=...)"]
 2 [label="c"]
 3 [label="b"]
 4 [label="...+"]
 5 [label="$"]
 6 [label="Match"]
 7 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 3
 4 -> 5
 5 -> 6
 2 -> 7
}""")
        
    def test_stateful_count(self):
        self.assert_graphs(parse('ab{1,2}c'), 
"""digraph {
 0 [label="a"]
 1 [label="{1,2}"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_lazy_stateful_count(self):
        self.assert_graphs(parse('ab{1,2}?c'), 
"""digraph {
 0 [label="a"]
 1 [label="{1,2}?"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_stateful_open_count(self):
        self.assert_graphs(parse('ab{1,}c'), 
"""digraph {
 0 [label="a"]
 1 [label="{1,}"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_stateful_fixed_count(self):
        self.assert_graphs(parse('ab{2}c'), 
"""digraph {
 0 [label="a"]
 1 [label="{2}"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")

    def test_stateful_group_count(self):
        self.assert_graphs(parse('a(?:bc){1,2}d'), 
"""digraph {
 0 [label="a"]
 1 [label="{1,2}"]
 2 [label="d"]
 3 [label="bc"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_stateless_count(self):
        self.assert_graphs(parse('ab{1,2}c',
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="ab"]
 1 [label="...?"]
 2 [label="b"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 3
}""")
        self.assert_graphs(parse('ab{1,2}c(?_l)'), 
"""digraph {
 0 [label="ab"]
 1 [label="...?"]
 2 [label="b"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 3
}""")
        
    def test_stateless_open_count(self):
        self.assert_graphs(parse('ab{3,}c',
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="abbb"]
 1 [label="...*"]
 2 [label="b"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 1
}""")
        
    def test_stateless_fixed_count(self):
        self.assert_graphs(parse('ab{2}c',
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="abbc"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_stateless_group_count(self):
        self.assert_graphs(parse('a(?:bc){1,2}d',
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="abc"]
 1 [label="...?"]
 2 [label="bc"]
 3 [label="d"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 3
}""")
        
    def test_lazy_stateless_count(self):
        self.assert_graphs(parse('ab{1,2}?c', 
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="ab"]
 1 [label="...??"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 2
 2 -> 4
}""")
        
    def test_lazy_stateless_open_count(self):
        self.assert_graphs(parse('ab{3,}?c', 
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="abbb"]
 1 [label="...*?"]
 2 [label="c"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_lazy_stateless_fixed_count(self):
        self.assert_graphs(parse('ab{2}?c', 
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="abbc"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_lazy_stateless_group_count(self):
        self.assert_graphs(parse('a(?:bc){1,2}?d',
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="abc"]
 1 [label="...??"]
 2 [label="d"]
 3 [label="bc"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 2
 2 -> 4
}""")
        
    def test_octal_escape(self):
        self.assert_graphs(parse('a\\075c'), 
"""digraph {
 0 [label="a=c"]
 1 [label="Match"]
 0 -> 1
}""")
        self.assert_graphs(parse('a\\142c'), 
"""digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")
        self.assert_graphs(parse('a\\142c', engine=DummyEngine), 
"""digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="c"]
 3 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
}""")

    def test_numbered_groups(self):
        self.assert_graphs(parse('a(b)c\\1d'), 
"""digraph {
 0 [label="a"]
 1 [label="(?P<1>"]
 2 [label="b"]
 3 [label=")"]
 4 [label="c"]
 5 [label="\\\\1"]
 6 [label="d"]
 7 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 7
}""")
        
    def test_simple_escape(self):
        self.assert_graphs(parse('a\\nc'), 
"""digraph {
 0 [label="a\\\\nc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_conditional(self):
        # in all cases, "no" is the first alternative
        self.assert_graphs(parse('(a)(?(1)b)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="a"]
 2 [label=")"]
 3 [label="(?(1)...)"]
 4 [label="Match"]
 5 [label="b"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 3 -> 5
 5 -> 4
}""")
        self.assert_graphs(parse('(a)(?(1)b|cd)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="a"]
 2 [label=")"]
 3 [label="(?(1)...|...)"]
 4 [label="cd"]
 5 [label="b"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 3 -> 5
 5 -> 6
 4 -> 6
}""")
        # so here, 'no' goes to b and is before the direct jump to Match
        # (3->4 before 3->5)
        self.assert_graphs(parse('(a)(?(1)|b)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="a"]
 2 [label=")"]
 3 [label="(?(1)|...)"]
 4 [label="b"]
 5 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 3 -> 5
 4 -> 5
}""")
        self.assert_graphs(parse('(a)(?(1)|)'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="a"]
 2 [label=")"]
 3 [label="(?(1)|)"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 3 -> 4
}""")
        self.assert_graphs(parse('(a)(?(1))'),
"""digraph {
 0 [label="(?P<1>"]
 1 [label="a"]
 2 [label=")"]
 3 [label="(?(1)|)"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 3 -> 4
}""")
        
    def test_character_escape(self):
        self.assert_graphs(parse(r'\A\b\B\d\D\s\S\w\W\Z'), 
"""digraph {
 0 [label="^"]
 1 [label="\\\\b"]
 2 [label="\\\\B"]
 3 [label="\\\\d"]
 4 [label="\\\\D"]
 5 [label="\\\\s"]
 6 [label="\\\\S"]
 7 [label="\\\\w"]
 8 [label="\\\\W"]
 9 [label="$"]
 10 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 7
 7 -> 8
 8 -> 9
 9 -> 10
}""")

    def test_named_group_bug(self):
        self.assert_graphs(parse('(?P<quote>)(?(quote))'), 
"""digraph {
 0 [label="(?P<1>"]
 1 [label=")"]
 2 [label="(?(quote)|)"]
 3 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 2 -> 3
}""")
        
    def test_pickle_bug(self):
        self.assert_graphs(parse('(?:b|c)+'), 
"""digraph {
 0 [label="...|..."]
 1 [label="b"]
 2 [label="c"]
 3 [label="...+"]
 4 [label="Match"]
 0 -> 1
 0 -> 2
 2 -> 3
 3 -> 0
 3 -> 4
 1 -> 3
}""")
        self.assert_graphs(parse('a(?:b|(c|e){1,2}?|d)+?(.)', 
                                 flags=ParserState._LOOP_UNROLL), 
"""digraph {
 0 [label="a"]
 1 [label="...|..."]
 2 [label="b"]
 3 [label="(?P<1>"]
 4 [label="d"]
 5 [label="...+?"]
 6 [label="(?P<2>"]
 7 [label="."]
 8 [label=")"]
 9 [label="Match"]
 10 [label="...|..."]
 11 [label="c"]
 12 [label="e"]
 13 [label=")"]
 14 [label="...??"]
 15 [label="(?P<1>"]
 16 [label="...|..."]
 17 [label="c"]
 18 [label="e"]
 19 [label=")"]
 0 -> 1
 1 -> 2
 1 -> 3
 1 -> 4
 4 -> 5
 5 -> 6
 5 -> 1
 6 -> 7
 7 -> 8
 8 -> 9
 3 -> 10
 10 -> 11
 10 -> 12
 12 -> 13
 13 -> 14
 14 -> 5
 14 -> 15
 15 -> 16
 16 -> 17
 16 -> 18
 18 -> 19
 19 -> 5
 17 -> 19
 11 -> 13
 2 -> 5
}""")
        
    def test_check_point(self):
        self.assert_graphs(parse('(a|b)*'), 
"""digraph {
 0 [label="...*"]
 1 [label="(?P<1>"]
 2 [label="Match"]
 3 [label="...|..."]
 4 [label="a"]
 5 [label="b"]
 6 [label=")"]
 0 -> 1
 0 -> 2
 1 -> 3
 3 -> 4
 3 -> 5
 5 -> 6
 6 -> 0
 4 -> 6
}""")
        self.assert_graphs(parse('(?(1)(a))*', flags=ParserState._EMPTY), 
"""digraph {
 0 [label="...*"]
 1 [label="(?(1)...)"]
 2 [label="Match"]
 3 [label="!"]
 4 [label="(?P<1>"]
 5 [label="a"]
 6 [label=")"]
 0 -> 1
 0 -> 2
 1 -> 3
 1 -> 4
 4 -> 5
 5 -> 6
 6 -> 3
 3 -> 0
}""")
        self.assert_graphs(parse('(?(1)(a))*', flags=ParserState._EMPTY|ParserState._UNSAFE), 
"""digraph {
 0 [label="...*"]
 1 [label="(?(1)...)"]
 2 [label="Match"]
 3 [label="(?P<1>"]
 4 [label="a"]
 5 [label=")"]
 0 -> 1
 0 -> 2
 1 -> 0
 1 -> 3
 3 -> 4
 4 -> 5
 5 -> 0
}""")
        
    def test_empty_bug(self):
        self.assert_graphs(parse('(?_l_e)a{0,1}*'), 
"""digraph {
 0 [label="...*"]
 1 [label="...?"]
 2 [label="Match"]
 3 [label="a"]
 4 [label="!"]
 0 -> 1
 0 -> 2
 1 -> 3
 1 -> 4
 4 -> 0
 3 -> 4
}""")

    def test_merge_clone_bug(self):
        self.assert_graphs(parse('(?_l)(?:a?){1,2}'), 
"""digraph {
 0 [label="...?"]
 1 [label="a"]
 2 [label="...?"]
 3 [label="...?"]
 4 [label="Match"]
 5 [label="a"]
 0 -> 1
 0 -> 2
 2 -> 3
 2 -> 4
 3 -> 5
 3 -> 4
 5 -> 4
 1 -> 2
}""")
        
    def test_ascii_escapes_bug(self):
        self.assert_graphs(parse(r'(\s*(\b\w+\b)\s*){3}',
                                 flags=ParserState._LOOP_UNROLL|ParserState.ASCII), 
"""digraph {
 0 [label="(?P<1>"]
 1 [label="...*"]
 2 [label="\\\\s"]
 3 [label="(?P<2>"]
 4 [label="\\\\b"]
 5 [label="\\\\w"]
 6 [label="...+"]
 7 [label="\\\\b"]
 8 [label=")"]
 9 [label="...*"]
 10 [label="\\\\s"]
 11 [label=")"]
 12 [label="(?P<1>"]
 13 [label="...*"]
 14 [label="\\\\s"]
 15 [label="(?P<2>"]
 16 [label="\\\\b"]
 17 [label="\\\\w"]
 18 [label="...+"]
 19 [label="\\\\b"]
 20 [label=")"]
 21 [label="...*"]
 22 [label="\\\\s"]
 23 [label=")"]
 24 [label="(?P<1>"]
 25 [label="...*"]
 26 [label="\\\\s"]
 27 [label="(?P<2>"]
 28 [label="\\\\b"]
 29 [label="\\\\w"]
 30 [label="...+"]
 31 [label="\\\\b"]
 32 [label=")"]
 33 [label="...*"]
 34 [label="\\\\s"]
 35 [label=")"]
 36 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
 6 -> 5
 6 -> 7
 7 -> 8
 8 -> 9
 9 -> 10
 9 -> 11
 11 -> 12
 12 -> 13
 13 -> 14
 13 -> 15
 15 -> 16
 16 -> 17
 17 -> 18
 18 -> 17
 18 -> 19
 19 -> 20
 20 -> 21
 21 -> 22
 21 -> 23
 23 -> 24
 24 -> 25
 25 -> 26
 25 -> 27
 27 -> 28
 28 -> 29
 29 -> 30
 30 -> 29
 30 -> 31
 31 -> 32
 32 -> 33
 33 -> 34
 33 -> 35
 35 -> 36
 34 -> 33
 26 -> 25
 22 -> 21
 14 -> 13
 10 -> 9
 2 -> 1
}""")
     
    def test_duplicate_group(self):
        self.assert_graphs(parse(r'(?P<a>.)(?P<a>.)'), 
"""digraph {
 0 [label="(?P<1>"]
 1 [label="."]
 2 [label=")"]
 3 [label="(?P<1>"]
 4 [label="."]
 5 [label=")"]
 6 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 5 -> 6
}""")
        
    def assert_flags(self, regexp, flags):
        (state, _graph) = parse(regexp)
        assert state.flags == flags, state.flags 
        
    def test_flags(self):
        self.assert_flags('', 0)
        self.assert_flags('(?i)', ParserState.IGNORECASE)
        try:
            self.assert_flags('(?L)', 0)
            assert False
        except RxpyException:
            pass
        self.assert_flags('(?m)', ParserState.MULTILINE)
        self.assert_flags('(?s)', ParserState.DOTALL)
        self.assert_flags('(?u)', ParserState.UNICODE)
        self.assert_flags('(?x)', ParserState.VERBOSE)
        self.assert_flags('(?a)', ParserState.ASCII)
        self.assert_flags('(?_l)', ParserState._LOOP_UNROLL)
        try:
            self.assert_flags('(?imsuxa_l)', 0)
            assert False
        except RxpyException:
            pass
        self.assert_flags('(?imsux_l)', 
                          ParserState.IGNORECASE | ParserState.MULTILINE | 
                          ParserState.DOTALL | ParserState.UNICODE |
                          ParserState.VERBOSE | ParserState._LOOP_UNROLL)
