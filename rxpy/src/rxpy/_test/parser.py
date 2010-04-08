
from rxpy._test.lib import GraphTest

from rxpy.parser import parse


class ParserTest(GraphTest):
    
    def test_sequence(self):
        self.assert_graphs(repr(parse('abc')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="None"]
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
 5 [label="None"]
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
 9 [label="None"]
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
 7 [label="None"]
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
 4 [label="None"]
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
 4 [label="None"]
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
 4 [label="None"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
}""")
        
    def test_non_matching_group(self):
        self.assert_graphs(repr(parse('a(?b)c')), 
"""strict digraph {
 0 [label="abc"]
 1 [label="None"]
 0 -> 1
}""")

    def test_character_plus(self):
        self.assert_graphs(repr(parse('ab+c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="b"]
 2 [label="(?b)+"]
 3 [label="c"]
 4 [label="None"]
 0 -> 1
 1 -> 2
 2 -> 3
 2 -> 1
 3 -> 4
}""")
        
    def test_character_star(self):
        self.assert_graphs(repr(parse('ab*c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?b)*"]
 2 [label="c"]
 3 [label="b"]
 4 [label="None"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 1
 2 -> 4
}""")
        
    def test_character_question(self):
        self.assert_graphs(repr(parse('ab?c')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?b)?"]
 2 [label="c"]
 3 [label="b"]
 4 [label="None"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 2
 2 -> 4
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
 6 [label="None"]
 0 -> 1
 1 -> 2
 2 -> 3
 3 -> 4
 4 -> 5
 4 -> 1
 5 -> 6
}""")
        
    def test_group_star(self):
        self.assert_graphs(repr(parse('a(bc)*d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?(bc))*"]
 2 [label="d"]
 3 [label="("]
 4 [label="bc"]
 5 [label=")"]
 6 [label="None"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 5
 5 -> 1
 2 -> 6
}""")
        
    def test_group_question(self):
        self.assert_graphs(repr(parse('a(bc)?d')), 
"""strict digraph {
 0 [label="a"]
 1 [label="(?(bc))?"]
 2 [label="d"]
 3 [label="("]
 4 [label="bc"]
 5 [label=")"]
 6 [label="None"]
 0 -> 1
 1 -> 2
 1 -> 3
 3 -> 4
 4 -> 5
 5 -> 2
 2 -> 6
}""")
        
        
