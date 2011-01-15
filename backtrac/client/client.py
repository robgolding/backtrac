import os, sys, socket

from twisted.python import util
from twisted.spread import pb
from twisted.spread.flavors import Referenceable
from twisted.internet.defer import Deferred, DeferredQueue
from twisted.internet.error import ConnectionRefusedError
from twisted.internet import reactor, inotify
from twisted.internet.task import deferLater, cooperate
from twisted.python import log
from twisted.python.filepath import FilePath
from twisted import cred

from utils import ConsumerQueue, TransferPager

class ClientError(Exception): pass

class BackupJob(object):
    CREATE = 0
    UPDATE = 1
    DELETE = 2

    def __init__(self, filepath, type=UPDATE):
        if isinstance(filepath, basestring):
            filepath = FilePath(filepath)
        self.filepath = filepath
        self.type = type

class TransferQueue(ConsumerQueue):
    def consumer(self, filepath):
        mtime = filepath.getModificationTime()
        size = filepath.getsize()
        r = self.perspective.callRemote('put_file', filepath.path, mtime, size)
        return r.addCallback(self._transfer, filepath)

    def _transfer(self, collector, filepath):
        print '%s, %d bytes' % (filepath.path, filepath.getsize())
        pager = TransferPager(collector, filepath)
        pager.wait()
        self.consume_next()

class BackupQueue(ConsumerQueue):
    def __init__(self, perspective, transfer_queue):
        super(BackupQueue, self).__init__(perspective)
        self.transfer_queue = transfer_queue

    def consumer(self, job):
        path = job.filepath.path
        mtime = job.filepath.getModificationTime()
        size = job.filepath.getsize()
        d = self.perspective.callRemote('check_file', path, mtime, size)
        d.addCallback(self._backup_file, job.filepath)
        self.consume_next()

    def _backup_file(self, backup_required, filepath):
        if backup_required:
            self.transfer_queue.add(filepath)

class BackupClient(pb.Referenceable):
    def __init__(self, server='localhost', port=8123,
                 hostname=socket.gethostname(), secret_key=''):
        self.server = server
        self.port = port
        self.hostname = hostname
        self.secret_key = secret_key
        self.connected = False
        self.notifier = inotify.INotify()

    def start(self):
        self.backup_queue.start()
        self.transfer_queue.start()
        self.perspective.callRemote('get_paths').addCallback(self._started)

    def handle_fs_event(self, watch, filepath, mask):
        if mask & inotify.IN_CREATE:
            type = BackupJob.CREATE
        elif mask & inotify.IN_MODIFY:
            type = BackupJob.UPDATE
        elif mask & inotify.IN_DELETE:
            type = BackupJob.DELETE
        else:
            return
        self.backup_queue.add(BackupJob(filepath, type=type))

    def _started(self, paths):
        for path in paths:
            self.notifier.watch(FilePath(path), autoAdd=True,
                                recursive=True,
                                callbacks=[self.handle_fs_event])
            for root, dirs, files in os.walk(path):
                for f in files:
                    path = os.path.join(root, f)
                    self.backup_queue.add(BackupJob(path))
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
        self.transfer_queue = TransferQueue(perspective)
        self.backup_queue = BackupQueue(perspective, self.transfer_queue)
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
