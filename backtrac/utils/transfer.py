import time

from twisted.spread.pb import Referenceable
from twisted.spread.util import FilePager
from twisted.internet.defer import Deferred

class TransferPager(FilePager):
    def __init__(self, collector, fd):
        FilePager.__init__(self, collector, fd, callback=self.done)
        self._deferred = Deferred()
        self.sendNextPage()

    def done(self):
        self._deferred.callback(self.collector)

    def wait(self):
        return self._deferred

class PageCollector(Referenceable):
    def __init__(self, fdst):
        self.fdst = fdst

    def remote_gotPage(self, page):
        self.fdst.write(page)

    def remote_endedPaging(self):
        self.fdst.close()
