import os, random

from twisted.internet import reactor
from twisted.spread import pb
from twisted.spread.pb import PBServerFactory 

from twisted.spread.util import FilePager
from twisted.internet.defer import Deferred

from utils import PageCollector

class BackupServer(pb.Root):
    def __init__(self, port=8123):
        self.port = port

    def start(self):
        reactor.listenTCP(self.port, PBServerFactory(BackupServer()))
        print 'Listening on port %d' % self.port
        reactor.run()

    def remote_backup(self, path):
        return random.random() > 0.5

    def remote_put_file(self, path):
        path = os.path.basename(path)
        collector = PageCollector(path)
        return collector


class BacktracDaemon(object): pass

if __name__ == '__main__':
    server = BackupServer()
    server.start()
