
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


from math import log, log10
from os.path import join
from time import time

from rxpy.engine._bench.re_python import _re as R_PYTHON
from rxpy.engine.backtrack.re_b import _re as R_B
from rxpy.engine.parallel.serial.re_ps import _re as R_PS
from rxpy.engine.parallel.serial.re_psh import _re as R_PSH
from rxpy.engine.parallel.beam.re_pb import _re as R_PB
from rxpy.engine.parallel.beam.re_pbh import _re as R_PBH
from rxpy.engine.parallel.wide.re_pw import _re as R_PW
from rxpy.engine.parallel.wide.re_pwh import _re as R_PWH


def execute(engines, benchmarks, trace=False, repeat=7):
    for benchmark in benchmarks:
        if trace: print benchmark
        def results():
            for engine in engines:
                if trace: print '.',
                secs = [benchmark(engine) for _i in range(repeat)]
                secs.sort()
                secs = secs[repeat/2]
                yield (engine, secs)
            if trace: print
        yield (benchmark, results())
    
        
def write(engines, benchmarks, directory='./'):
    for (benchmark, data) in execute(engines, benchmarks):
        with file(join(directory, str(benchmark) + '.dat'), 'w') as out:
            for (engine, secs) in data:
                print >> out, secs, ';', str(engine)
                
                
def text_histogram(engines, benchmarks):
    
    def right(text, width):
        text = str(text)
        l = len(text)
        if l > width:
            return text[0:width-3] + '...'
        else:
            return (width - l) * ' ' + text
        
    def lin_bar(x, all, l):
        m = max(all)
        x = int(float(x) / (float(m) / l) + 0.5)
        return min(l, max(x, 0))
        
    def log_bar(x, all, l):
        mn, mx = min(all), max(all)
        x = int(log(float(x) / mn) / log(float(mx) / mn) * l + 0.5)
        return min(l, max(x, 0))
    
    def bar(x, all, l):
        ln = lin_bar(x, all, l)
        lg = log_bar(x, all, l)
        line = ['#'] * ln
        if lg > ln:
            line += [' '] * (lg-ln-1) + [']']
        else:
            if line:
                line[-1] = ']'
        if line:
            if line[0] == ']':
                line[0] = '|'
            else:
                line[0] = '['
        return ''.join(line + [' '] * (l-lg))
        
    for (benchmark, data) in execute(engines, benchmarks):
        print
        print benchmark
        (engines, secs) = zip(*list(data))
        for (engine, sec) in zip(engines[1:], secs[1:]):
            print '{0} {1}{2:7.0f} [{3:3.1f}]'.format(
                right(engine, 25), bar(sec, secs, 40), 
                sec/secs[0], log10(sec/secs[0]))
            

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
        
    def __call__(self, engine):
        self.start()
        for _i in range(self._count):
            engine.compile(self._pattern)
        return self.finish()


class MatchBenchmark(CompileBenchmark):
    
    def __init__(self, name, pattern, count, text, search=False):
        super(MatchBenchmark, self).__init__(name, pattern, count)
        self._text = text
        self._search = search
        
    def __call__(self, engine):
        regexp = engine.compile(self._pattern)
        self.start()
        for _i in range(self._count):
            if self._search:
                regexp.search(self._text)
            else:
                regexp.match(self._text)
        return self.finish()
    
    
def exponential(n):
    return MatchBenchmark('Match a?^na^n against a^n for n=' + str(n), 
                          n * 'a?' + n * 'a' * n, 1, n*'a')

def exponential2(n):
    return MatchBenchmark('Match (?:ab)?^n(?:ab)^n against (ab)^n for n=' + str(n), 
                          n * '(?:ab)?' + n * '(?:ab)', 1, n*'ab')

def exponential3(n):
    return MatchBenchmark('Match (?:a*b)?^n(?:a*b)^n against (ab)^n for n=' + str(n), 
                          n * '(?:a*b)?' + n * '(?:a*b)', 1, n*'ab')

def exponential4(n):
    return MatchBenchmark('Match (?:a|b)?^2n(?:ab)^n against (ab)^n for n=' + str(n), 
                          2 * n * '(?:a|b)?' + n * 'ab', 1, n*'ab')

def exponential5(n):
    return MatchBenchmark('Match (a|b)?^2n(?:ab)^n against (ab)^n for n=' + str(n), 
                          2 * n * '(a|b)?' + n * 'ab', 1, n*'ab')
    
def explore_python():
    for n in range(100):
        pattern = 2 * n * '(a|b)?' + n * 'ab'
        regexp = R_PYTHON.compile(pattern)
        start = time()
        regexp.match(n * 'ab')
        print n, time() - start

    

if __name__ == '__main__':
    text_histogram([R_PYTHON, R_B, R_PW, R_PWH, R_PS, R_PSH, R_PB, R_PBH], [
        MatchBenchmark('Match a(.)c against abc', 
                       'a(.)c', 100, 'abc'),
        MatchBenchmark('Match (a)b(?<=(?(1)b|x))(c) against abc',
                       '(a)b(?<=(?(1)b|x))(c)', 100, 'abc'),
        MatchBenchmark('Match a*b against a^100b', 
                       'a*b', 2, 100*'a' + 'b'),
        MatchBenchmark('Match .*b against a^100b', 
                       '.*b', 2, 100*'a' + 'b'),
        MatchBenchmark('Search .*b against a^100b', 
                       '.*b', 1, 100*'a' + 'b', search=True),
        MatchBenchmark('Match (.*) (.*) (.*)  against abc abc abc', 
                       '(.*) (.*) (.*)', 10, 'abc abc abc'),
        ])
    print
    text_histogram([R_PYTHON, R_B, R_PW, R_PWH, R_PS, R_PSH, R_PB, R_PBH], [
        MatchBenchmark('Search .*?a*b against a^10b', 
                       '.*?a*b', 1, 10*'a' + 'b', search=True),
        ])
    text_histogram([R_PYTHON, R_B, R_PWH, R_PS, R_PSH, R_PB, R_PBH], [
        MatchBenchmark('Search .*?a*b against a^100b', 
                       '.*?a*b', 1, 100*'a' + 'b', search=True),
        ])
    text_histogram([R_PYTHON, R_B, R_PWH, R_PSH, R_PB, R_PBH], [
        MatchBenchmark('Search .*?a*b against a^1000b', 
                       '.*?a*b', 1, 1000*'a' + 'b', search=True),
        ])
    print
    text_histogram([R_PYTHON, R_B, R_PW, R_PWH, R_PS, R_PSH, R_PB, R_PBH], [
        exponential5(4),
        ])
    text_histogram([R_PYTHON, R_B, R_PW, R_PWH, R_PS, R_PSH], [
        exponential5(6),
        ])
    print
    text_histogram([R_PYTHON, R_B, R_PW, R_PWH, R_PS, R_PSH, R_PB, R_PBH], [
        exponential4(4),
        ])
    text_histogram([R_PYTHON, R_B, R_PW, R_PWH, R_PS, R_PSH, R_PBH], [
        exponential4(6),
        ])
    text_histogram([R_PYTHON, R_PWH, R_PSH, R_PBH], [
        exponential4(8),
        exponential(8),
        ])
    