from twisted.spread.util import FilePager
from twisted.internet.defer import Deferred

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
