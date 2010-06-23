
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

from re import compile


class EscapeTest(TestCase):
    
    def test_literal_escape(self):
        '''
        This shows that the regexp interpreter itself expands literal escape
        characters.
        '''
        p = compile('a\\x62c')
        assert p.match('abc')
        assert not p.match('axc')
        assert p.match('a\x62c')
        
    def test_escape(self):
        '''
        Alternatively, the character can be simply used
        '''
        p = compile('a\x62c')
        assert p.match('abc')
        assert not p.match('axc')
        assert p.match('a\x62c')

    def test_slash_escape(self):
        '''
        See http://groups.google.com/group/comp.lang.python/browse_thread/thread/3a27b819307c0cb6#
        '''
        p = compile('a\\\x62c')
#        assert p.match('a\\bc')

    def test_nested_groups(self):
        p = compile('(.)*')
        m = p.match('ab')
        assert m
        assert m.groups() == ('b',), m.groups()
        assert m.group(0) == 'ab', m.group(0)
        assert m.group(1) == 'b', m.group(1)
        
        p = compile(r'(?:\s*(\b\w+\b)\s*){3}')
        m = p.match('foo bar baz ')
        assert m
        assert m.groups() == ('baz',), m.groups()
        
        p = compile(r'(?:\s*(\b\w*\b)\s*){3}')
        m = p.match(' a ab abc ')
        assert m.group(0) == ' a ab abc ', m.group(0)
        
#        p = compile('(\b.*?\b)*')
#        m = p.match(' a  ab  abc ')
#        assert m.groups() == ('abc'), m.groups()
        