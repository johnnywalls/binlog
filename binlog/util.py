from functools import wraps


class MaskException:
    def __init__(self, exp, mask):
        self.exp = exp
        self.mask = mask

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwds):
            try:
                return f(*args, **kwds)
            except self.exp as exc:
                raise self.mask from exc
        return wrapper

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is self.exp:
            raise self.mask from exc_type


def popminleft(a, b):
    if a and b:
        if a[0].L <= b[0].L:
            return a.popleft()
        else:
            return b.popleft()
    elif a:
        return a.popleft()
    elif b:
        return b.popleft()
    else:
        return None


def cmp(a, b):                                                              
    """ http://codegolf.stackexchange.com/a/49779 """                       
    return (a > b) - (a < b)
