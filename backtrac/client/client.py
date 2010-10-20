import os
from threading import Thread

from twisted.python import util
from twisted.spread import pb
from twisted.spread.util import FilePager
from twisted.spread.flavors import Referenceable
from twisted.internet.defer import Deferred, DeferredQueue
from twisted.internet import reactor
from twisted.internet.task import deferLater, cooperate
from twisted.python import log
from twisted.cred import credentials

class TransferPager(FilePager):
    def __init__(self, collector, path):
        self._deferred = Deferred()
        print "%s, %d bytes" % (path, os.path.getsize(path))
        fd = open(path, 'rb')
        p = FilePager.__init__(self, collector, fd, callback=self.done)
        self.sendNextPage()

    def done(self):
        print 'File sent!'
        self._deferred.callback(self.collector)

    def wait(self):
        return self._deferred

class FileTransferAgent(object):
    def __init__(self, perspective):
        self.perspective = perspective

    def send(self, path):
        r = self.perspective.callRemote('put_file', path)
        return r.addCallback(self._transfer, path)

    def _transfer(self, collector, path):
        return TransferPager(collector, path).wait()
    
    def _done(self):
        print 'Done!'

class BackupClient(pb.Referenceable):
    def __init__(self, server, path):
        self.server = server
        self.path = path
        self.queue = DeferredQueue()
        self.connected = False

    def _queue_consumer(self, path):
        def p(m): print 'Echoed:', m
        d = self.server.callRemote('echo', path)
        d.addCallback(p)
        self.queue.get().addCallback(self._queue_consumer)

    def backup_file(self, result, path):
        if result:
            print 'Sending: %s' % path
            self.transfer.send(path)
        else:
            print 'Skipping: %s' % path

    def start(self):
        self.queue.get().addCallback(self._queue_consumer)
        for root, dirs, files in os.walk(self.path):
            for f in files:
                path = os.path.join(root, f)
                #self.queue.put(path)
                d = self.perspective.callRemote('backup_file', path)
                d.addCallback(self.backup_file, path)

    def connect(self, start_on_connect=False):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.server, 8123, factory)
        d = factory.login(credentials.UsernamePassword("armstrong", "password"),
                         client=self)
        d.addCallback(self._connected, start_on_connect)
        reactor.run()

    def _connected(self, perspective, start_client=False):
        self.connected = True
        self.perspective = perspective
        self.transfer = FileTransferAgent(perspective)
        print 'Connected to %s' % self.server
        if start_client:
            self.start()

if __name__ == '__main__':
    client = BackupClient("localhost", "/home/rob/Desktop")
    client.connect(True)
