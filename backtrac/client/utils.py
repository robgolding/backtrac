from twisted.spread.util import FilePager
from twisted.internet.defer import Deferred, DeferredQueue

class ConsumerQueue(object):
    def __init__(self, perspective):
        self.perspective = perspective
        self.queue = DeferredQueue()

    def add(self, filepath):
        self.queue.put(filepath)

    def consume_next(self):
        self.queue.get().addCallback(self.consumer)

    def consumer(self, obj):
        raise NotImplementedError

    def start(self):
        self.consume_next()

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
