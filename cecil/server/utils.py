import os

from twisted.spread.flavors import Referenceable

class PageCollector(Referenceable):
    def __init__(self, path):
        self.path = path
        self.fd = None

    def remote_gotPage(self, page):
        print 'Writing page (%d bytes)' % len(page)
        if self.fd is None:
            self.fd = open(self.path, 'wb')
        self.fd.write(page)
        return

    def remote_endedPaging(self):
        if self.fd is not None:
            self.fd.close()
        print 'Received file'
        return
