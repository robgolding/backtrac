import time

from twisted.spread.util import FilePager
from twisted.internet.defer import Deferred, DeferredQueue

class TimoutExpiredException(Exception): pass

def get_result_blocking(d, timeout=1500, interval=0.1):
    start = time.time()
    while not d.called:
        if time.time() > (start + timeout):
            raise TimeoutExpiredException()
        time.sleep(interval)
    return d.result
