

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
