

from rxpy._test.lib import GraphTest
from rxpy.graph import String


class ReprTest(GraphTest):
    
    def test_sequence(self):
        self.assert_graphs(repr(String('a').concatenate(String('b'))),
"""strict digraph {
 0 [label="a"]
 1 [label="b"]
 0 -> 1
}""")
