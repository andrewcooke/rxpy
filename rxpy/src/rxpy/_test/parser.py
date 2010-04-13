
from rxpy._test.lib import GraphTest

from rxpy.parser import parse


class ParserTest(GraphTest):
    
    def test_sequence(self):
        self.assert_graphs(repr(parse('abc')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")
    
    def test_matching_group(self):
        self.assert_graphs(repr(parse('a(b)c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
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
        self.assert_graphs(repr(parse('a(b(c)d)e')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
 2 [label="b"]
 3 [label="("]
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
        self.assert_graphs(repr(parse('a((b))c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
 2 [label="("]
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
        self.assert_graphs(repr(parse('a(b)')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
 2 [label="b"]
 3 [label=")"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")

    def test_matching_group_early_open(self):
        self.assert_graphs(repr(parse('(a)b')), 
"""strict digraph {
 0 [label="("]
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
        self.assert_graphs(repr(parse('a()b')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
 2 [label=")"]
 3 [label="b"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")
        
    def test_non_matching_group(self):
        self.assert_graphs(repr(parse('a(?b)c')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_character_plus(self):
        self.assert_graphs(repr(parse('ab+c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="(?b)+"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 1
 2 -> 3
 3 -> 4
}""")


    def test_character_star(self):
        self.assert_graphs(repr(parse('ab*c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?b)*"]
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
        self.assert_graphs(repr(parse('ab?c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?b)?"]
 2 [label="b"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 2 -> 3
}""")
        
    def test_group_plus(self):
        self.assert_graphs(repr(parse('a(bc)+d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
 2 [label="bc"]
 3 [label=")"]
 4 [label="(?(bc))+"]
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
        self.assert_graphs(repr(parse('a(bc)*d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?(bc))*"]
 2 [label="("]
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
        self.assert_graphs(repr(parse('a(bc)?d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?(bc))?"]
 2 [label="("]
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
        self.assert_graphs(repr(parse('[a-z]')), 
"""strict digraph {
 0 [label="[a-z]"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_double_range(self):
        self.assert_graphs(repr(parse('[a-c][p-q]')), 
"""strict digraph {
 0 [label="[a-c]"]
 1 [label="[pq]"]
 2 [label="Match"]
 0 -> 1
 1 -> 2
}""")    

    def test_single_range(self):
        self.assert_graphs(repr(parse('[a]')), 
"""strict digraph {
 0 [label="a"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_inverted_range(self):
        self.assert_graphs(repr(parse('[^apz]')), 
r"""strict digraph {
 0 [label="[\\x00-`b-oq-y{-\\U0010ffff]"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_escaped_range(self):
        self.assert_graphs(repr(parse(r'[\x00-`b-oq-y{-\U0010ffff]')), 
r"""strict digraph {
 0 [label="[\\x00-`b-oq-y{-\\U0010ffff]"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_x_escape(self):
        self.assert_graphs(repr(parse('a\\x62c')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_u_escape(self):
        self.assert_graphs(repr(parse('a\\u0062c')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_U_escape(self):
        self.assert_graphs(repr(parse('a\\U00000062c')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="Match"]
 0 -> 1
}""")

    def test_escaped_escape(self):
        self.assert_graphs(repr(parse('\\\\')), 
# unsure about this...
"""strict digraph {
 0 [label="\\\\\\\\"]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_dot(self):
        self.assert_graphs(repr(parse('.')), 
"""strict digraph {
 0 [label="."]
 1 [label="Match"]
 0 -> 1
}""")
        
    def test_lazy_character_plus(self):
        self.assert_graphs(repr(parse('ab+?c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="(?b)+?"]
 3 [label="c"]
 4 [label="Match"]
 0 -> 1
 1 -> 2
 2 -> 3
 2 -> 1
 3 -> 4
}""")


    def test_lazy_character_star(self):
        self.assert_graphs(repr(parse('ab*?c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?b)*?"]
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
        self.assert_graphs(repr(parse('ab??c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?b)??"]
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
        self.assert_graphs(repr(parse('a(bc)+?d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="("]
 2 [label="bc"]
 3 [label=")"]
 4 [label="(?(bc))+?"]
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
        self.assert_graphs(repr(parse('a(bc)*?d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?(bc))*?"]
 2 [label="d"]
 3 [label="("]
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
        self.assert_graphs(repr(parse('a|b|cd')), 
"""strict digraph {
 0 [label="a|b|cd"]
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
        self.assert_graphs(repr(parse('(a|b|cd)')),
"""strict digraph {
 0 [label="("]
 1 [label="a|b|cd"]
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
        
    def test_nested_groups(self):
        self.assert_graphs(repr(parse('a|(b|cd)')),
"""strict digraph {
 0 [label="a|(b|cd)"]
 1 [label="a"]
 2 [label="("]
 3 [label="b|cd"]
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
