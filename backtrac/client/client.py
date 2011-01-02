import os, sys, socket

from twisted.python import util
from twisted.spread import pb
from twisted.spread.util import FilePager
from twisted.spread.flavors import Referenceable
from twisted.internet.defer import Deferred, DeferredQueue
from twisted.internet.error import ConnectionRefusedError
from twisted.internet import reactor, inotify
from twisted.internet.task import deferLater, cooperate
from twisted.python import log, filepath
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
        stat = os.stat(path)
        r = self.perspective.callRemote('put_file', path, stat[8], stat[6])
        return r.addCallback(self._transfer, path)

    def _transfer(self, collector, path):
        return TransferPager(collector, path).wait()

    def _done(self):
        print 'Done!'

class BackupClient(pb.Referenceable):
    def __init__(self, server='localhost', port=8123,
                 hostname=socket.gethostname(), secret_key=''):
        self.server = server
        self.port = port
        self.hostname = hostname
        self.secret_key = secret_key
        self.connected = False
        self.queue = DeferredQueue()
        self.notifier = inotify.INotify()

    def backup_file(self, backup_required, path):
        if backup_required:
            print 'Sending: %s' % path
            self.transfer.send(path)

    def start(self):
        self.perspective.callRemote('get_paths').addCallback(self._started)

    def handle_fs_event(self, watch, filepath, mask):
        if mask & inotify.IN_MODIFY:
            self.queue.put(filepath.path)

    def consumer(self, path):
        stat = os.stat(path)
        d = self.perspective.callRemote('check_file', path, stat[8], stat[6])
        d.addCallback(self.backup_file, path)
        self.queue.get().addCallback(self.consumer)

    def _started(self, paths):
        self.queue.get().addCallback(self.consumer)
        for path in paths:
            self.notifier.watch(filepath.FilePath(path), autoAdd=True,
                                recursive=True,
                                callbacks=[self.handle_fs_event])
            for root, dirs, files in os.walk(path):
                for f in files:
                    path = os.path.join(root, f)
                    self.queue.put(path)
        self.notifier.startReading()

    def connect(self, start_on_connect=False):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.server, self.port, factory)
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
