# coding: utf-8

import time
from functools import wraps

def exec_time(f):
    @wraps(f)
    def _inner(*args, **kwargs):
        start_t = time.time()
        func_result = f(*args, **kwargs)
        exec_t = time.time() - start_t
        print "Function %s : finished in %s" % (f.__name__, exec_t)
        return func_result
    return _inner