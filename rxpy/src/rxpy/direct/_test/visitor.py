
from unittest import TestCase

from rxpy.alphabet.unicode import Unicode
from rxpy.direct.visitor import Visitor, Fail
from rxpy.parser._test.parser import parse


class VisitorTest(TestCase):
    
    def test_string(self):
        Visitor(Unicode(), parse('abc'), 'abc')
        Visitor(Unicode(), parse('abc'), 'abcd')
        try:
            Visitor(Unicode(), parse('abc'), 'ab')
            assert False, 'expected failure'
        except Fail:
            pass
