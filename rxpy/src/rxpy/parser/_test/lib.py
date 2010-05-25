
from __future__ import print_function
from unittest import TestCase

from gv import readstring, render, layout


class GraphTest(TestCase):
    
    def assert_graphs(self, result, target):
        ok = result == target
        if not ok:
            print('target:\n' + target)
            print('result:\n' + result)
            try:
                graph = readstring(result)
                layout(graph, 'neato')
                render(graph, 'gtk')
            except Exception, e:
                print(e)
            assert False
