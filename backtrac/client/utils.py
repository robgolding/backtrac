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

class TransferPager(FilePager):
    def __init__(self, collector, filepath):
        self._deferred = Deferred()
        fd = open(filepath.path, 'rb')
        p = FilePager.__init__(self, collector, fd, callback=self.done)
        self.sendNextPage()

    def done(self):
        self._deferred.callback(self.collector)

    def wait(self):
        return self._deferred
