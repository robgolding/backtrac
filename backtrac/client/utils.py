from twisted.spread.util import FilePager
from twisted.internet.defer import Deferred, DeferredQueue

class ConsumerQueue(object):
    def __init__(self, stop_on_error=False):
        self.stop_on_error = stop_on_error
        self.queue = DeferredQueue()

    def _consume_next(self, *args):
        self.queue.get().addCallbacks(self._consumer, self._error)

    def _consumer(self, obj):
        self.consume(obj)
        self._consume_next()

    def _error(self, fail):
        self.error(fail)
        if not self.stop_on_error:
            self._consume_next()

    def add(self, filepath):
        self.queue.put(filepath)

    def consume(self, obj):
        raise NotImplementedError
    
    def fail(self, fail):
        raise NotImplementedError

    def start(self):
        self._consume_next()

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
