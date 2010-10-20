import os, sys, socket
from threading import Thread

from twisted.python import util
from twisted.spread import pb
from twisted.spread.util import FilePager
from twisted.spread.flavors import Referenceable
from twisted.internet.defer import Deferred, DeferredQueue
from twisted.internet.error import ConnectionRefusedError
from twisted.internet import reactor
from twisted.internet.task import deferLater, cooperate
from twisted.python import log
from twisted import cred

class ClientError(Exception): pass

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
    def __init__(self, server='localhost',
                 hostname=socket.gethostname(), secret_key=''):
        self.server = server
        self.hostname = hostname
        self.secret_key = secret_key
        self.connected = False

    def backup_file(self, result, path):
        if result:
            print 'Sending: %s' % path
            self.transfer.send(path)
        else:
            print 'Skipping: %s' % path

    def start(self):
        self.perspective.callRemote('get_paths').addCallback(self._started)

    def _started(self, paths):
        for path in paths:
            for root, dirs, files in os.walk(path):
                for f in files:
                    path = os.path.join(root, f)
                    d = self.perspective.callRemote('backup_file', path)
                    d.addCallback(self.backup_file, path)

    def connect(self, start_on_connect=False):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.server, 8123, factory)
        d = factory.login(
            cred.credentials.UsernamePassword(
                self.hostname,
                self.secret_key
            ),
            client=self
        )
        d.addCallback(self._connected, start_on_connect)
        d.addErrback(self._error)
        reactor.run()

    def _connected(self, perspective, start_client=False):
        self.connected = True
        self.perspective = perspective
        self.transfer = FileTransferAgent(perspective)
        print 'Connected to %s' % self.server
        if start_client:
            self.start()

    def _error(self, error):
        if error.type == 'twisted.cred.error.UnauthorizedLogin':
            print >>sys.stderr, 'Failed to authenticate with server: %s' % self.server
        elif error.type == ConnectionRefusedError:
            print >>sys.stderr, 'Connection refused when connecting to server: %s' % self.server
        else:
            print >>sys.stderr, error.getTraceback()
        reactor.stop()

if __name__ == '__main__':
    client = BackupClient(server='localhost', secret_key='password')
    client.connect(True)
