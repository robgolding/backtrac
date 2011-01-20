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

from backtrac.apps.catalog.utils import normpath

class ClientError(Exception): pass

class BackupJob(object):
    MODIFY = 0
    DELETE = 1

    def __init__(self, filepath, type=MODIFY):
        if isinstance(filepath, basestring):
            filepath = FilePath(filepath)
        self.filepath = filepath
        self.type = type

class BackupQueue(ConsumerQueue):
    def __init__(self, client, *args, **kwargs):
        super(BackupQueue, self).__init__(*args, **kwargs)
        self.client = client

    def consume(self, job):
        path = job.filepath.path
        if job.type == BackupJob.MODIFY:
            mtime = job.filepath.getModificationTime()
            size = job.filepath.getsize()
            d = self.client.perspective.callRemote('check_file', path, mtime,
                                                   size)
            d.addCallback(self._check_result, path)
        elif job.type == BackupJob.DELETE:
            print '%s deleted' % path
            self.client.perspective.callRemote('delete_file', path)

    def _check_result(self, backup_required, path):
        if backup_required:
            self.client.transfer_queue.add(FilePath(path))

class TransferQueue(BackupQueue):
    def consume(self, filepath):
        mtime = filepath.getModificationTime()
        size = filepath.getsize()
        d = self.client.perspective.callRemote('put_file', filepath.path, mtime,
                                               size)
        d.addCallback(self._transfer, filepath)

    def _transfer(self, collector, filepath):
        print '%s, %d bytes' % (filepath.path, filepath.getsize())
        pager = TransferPager(collector, filepath)
        pager.wait()

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
        if mask & inotify.IN_CHANGED or mask & inotify.IN_MOVED_TO:
            type = BackupJob.MODIFY
        elif mask & inotify.IN_DELETE or mask & inotify.IN_MOVED_FROM:
            type = BackupJob.DELETE
        else:
            return
        self.backup_queue.add(BackupJob(filepath, type=type))

    def _check_present_state(self, paths):
        for path in paths:
            if not os.path.exists(path):
                job = BackupJob(path, type=BackupJob.DELETE)
                self.backup_queue.add(job)

    def _check_result(self, result):
        path, required = result
        if required:
            self.transfer_queue.add(FilePath(path))

    def _started(self, paths):
        for path in paths:
            path = normpath(path)
            self.perspective.callRemote('get_present_state',
                                        path).addCallback(
                                            self._check_present_state)
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
        self.backup_queue = BackupQueue(self)
        self.transfer_queue = TransferQueue(self)
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
