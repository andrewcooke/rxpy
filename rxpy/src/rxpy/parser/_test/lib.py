
from __future__ import print_function
from unittest import TestCase

from gv import readstring, render, layout


class GraphTest(TestCase):
    
    def assert_graphs(self, result, target):
        (_alphabet, _flags, graph) = result
        graph = repr(graph)
        ok = graph == target
        if not ok:
            print('target:\n' + target)
            print('result:\n' + graph)
            try:
                graph = readstring(graph)
                layout(graph, 'neato')
                render(graph, 'gtk')
            except Exception, e:
                print(e)
            assert False
