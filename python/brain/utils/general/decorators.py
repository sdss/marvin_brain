
from functools import wraps
from brain.core.exceptions import BrainError

try:
    from sdss_access.path import Path
except ImportError:
    Path = None

# General Decorators
__all__ = ['public', 'parseRoutePath', 'checkPath']


def public(f):
    ''' Decorator to declare a route public '''
    f.is_public = True
    return f


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


def check_auth(func):
    ''' Decorator that checks if a valid netrc file exists

    Function Decorator to check if a valid netrc file exists.
    If not it raises an error.  Otherwise it
    returns the function and proceeds as normal.

    Returns:
        The decorated function

    Raises:
        BrainError: You are not authorized to access the SDSS collaboration

    Example:
        >>>
        >>> @check_auth
        >>> def my_function():
        >>>     return 'I am working function'
        >>>

    '''

    from brain import bconfig
    @wraps(func)
    def wrapper(*args, **kwargs):
        # iscollab = bconfig.access == 'collab'
        valid_netrc = bconfig._check_netrc()
        if valid_netrc:
            return func(*args, **kwargs)
        else:
            raise BrainError('You are not authorized to access the SDSS collaboration')

    return wrapper

