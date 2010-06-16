

class UnsupportedOperation(Exception):
    '''
    Raised when some (hopefully optional) functionality is not supported.
    '''


class UnimplementedMethod(Exception):
    '''
    Raised when an "abstract" method is not implemented.
    '''


def unimplemented(method):
    def replacement(*args, **kargs):
        raise UnimplementedMethod(method)
    return replacement


class ParseException(Exception):
    '''
    General exception raised by all modules.
    '''
    
    
(I, M, S, U, X, A, _S, _B) = map(lambda x: 2**x, range(8))
(IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _STATEFUL, _BACKTRACK_OR) = (I, M, S, U, X, A, _S, _B)
_FLAGS = (I, M, S, U, X, A, _S, _B, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _STATEFUL, _BACKTRACK_OR)
