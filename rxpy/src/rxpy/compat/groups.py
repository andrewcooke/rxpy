
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


class Groups(object):
    
    def __init__(self, text=None, groups=None, offsets=None, count=0, 
                 names=None, indices=None, lastindex=None):
        self.__text = text
        self.__groups = groups if groups else {}
        self.__offsets = offsets if offsets else {}
        self.__count = count
        self.__names = names if names else {}
        self.__indices = indices if indices else {}
        self.__lastindex = lastindex
        
    def start_group(self, number, offset):
        self.__offsets[number] = offset
        
    def end_group(self, number, offset):
        assert isinstance(number, int)
        assert number in self.__offsets, 'Unopened group'
        self.__groups[number] = (self.__text[self.__offsets[number]:offset],
                                 self.__offsets[number], offset)
        del self.__offsets[number]
        if number: # avoid group 0
            self.__lastindex = number
    
    def __len__(self):
        return self.__count
    
    def __bool__(self):
        return bool(self.__groups)
    
    def __nonzero__(self):
        return self.__bool__()
    
    def clone(self):
        return Groups(text=self.__text, groups=dict(self.__groups), 
                      offsets=dict(self.__offsets), count=self.__count, 
                      names=self.__names, indices=self.__indices,
                      lastindex=self.__lastindex)
    
    def __getitem__(self, number):
        if number in self.__names:
            index = self.__names[number]
        else:
            index = number
        try:
            return self.__groups[index]
        except KeyError:
            if isinstance(index, int) and index <= self.__count:
                return [None, -1, -1]
            else:
                raise IndexError(number)
    
    def group(self, number, default=None):
        group = self[number][0]
        return default if group is None else group
        
    def start(self, number):
        return self[number][1]
    
    def end(self, number):
        return self[number][2]

    @property
    def lastindex(self):
        return self.__lastindex
    
    @property
    def lastgroup(self):
        return self.__indices.get(self.lastindex, None)
