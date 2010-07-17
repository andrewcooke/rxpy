
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


from os.path import join
from time import time

from rxpy.engine.backtrack.re import _re as R_BACKTRACK


def execute(engines, benchmarks):
    for benchmark in benchmarks:
        def results():
            for engine in engines:
                (secs, ticks, width) = benchmark(engine)
                yield (engine, secs, ticks, width)
        yield (benchmark, results())
    
        
def write(engines, benchmarks, directory='./'):
    for (engine, data) in execute(engines, benchmarks):
        with file(join(directory, str(engine) + '.dat'), 'w') as out:
            for (engine, secs, ticks, width) in data:
                print >> out, secs, ticks, width, str(engine)
            

class BaseBenchmark(object):
    
    def __init__(self, name, count):
        self.__name = name
        self._count = count
        
    def __str__(self):
        return self.__name
    
    def start(self):
        self.__start = time()

    def finish(self):
        return (time() - self.__start) / float(self._count)
    
    
class CompileBenchmark(BaseBenchmark):
    
    def __init__(self, name, pattern, count):
        super(CompileBenchmark, self).__init__(name, count)
        self._pattern = pattern
        
    def call(self, engine):
        self.start()
        for _i in range(self._count):
            engine.compile(self._pattern)
        return self.finish()


class MatchBenchmark(CompileBenchmark):
    
    def __init__(self, name, pattern, count, text, search=False):
        super(MatchBenchmark, self).__init__(name, pattern, count)
        self._text = text
        self._search = search
        
    def call(self, engine):
        regexp = engine.compile(self._pattern)
        self.start()
        for _i in range(self._count):
            if self._search:
                regexp.search(self._text)
            else:
                regexp.match(self._text)
        return self.finish()
    

C_ABC = CompileBenchmark('Compile a(.)c', 'a(.)c', 1000)
M_ABC = MatchBenchmark('Match a(.)c', 'a(.)c', 1000, 'abc')


if __name__ == '__main__':
    write([R_BACKTRACK], [C_ABC, M_ABC])

