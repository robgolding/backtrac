import os

from twisted.spread.flavors import Referenceable

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

class PageCollector(Referenceable):
    def __init__(self, fdst):
        self.fdst = fdst

    def remote_gotPage(self, page):
        self.fdst.write(page)

    def remote_endedPaging(self):
        self.fdst.close()
