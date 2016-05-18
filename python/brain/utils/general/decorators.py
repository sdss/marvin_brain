
from functools import wraps
from brain.core.exceptions import BrainError

try:
    from sdss_access.path import Path
except ImportError:
    Path = None

# General Decorators
__all__ = ['parseRoutePath', 'checkPath']


def parseRoutePath(f):
    ''' Decorator to parse generic route path '''
    @wraps(f)
    def decorated_function(inst, *args, **kwargs):
        if 'path' in kwargs and kwargs['path']:
            for kw in kwargs['path'].split('/'):
                if len(kw) == 0:
                    continue
                var, value = kw.split('=')
                kwargs[var] = value
        kwargs.pop('path')
        return f(inst, *args, **kwargs)
    return decorated_function


def checkPath(func):
    '''Decorator that checks if sdss_access Path has been imported '''

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not Path:
            raise BrainError('sdss_access is not installed')
        else:
            return func(*args, **kwargs)
    return wrapper
