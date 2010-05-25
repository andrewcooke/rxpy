

from rxpy._test.lib import GraphTest
from rxpy.graph import String
from rxpy.alphabet.unicode import Unicode


class ReprTest(GraphTest):
    
    def test_sequence(self):
        unicode = Unicode()
        self.assert_graphs(repr(String('a', unicode).concatenate(String('b', unicode))),
"""strict digraph {
 0 [label="a"]
 1 [label="b"]
 0 -> 1
}""")
