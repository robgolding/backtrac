import os
import sys
import socket

from twisted.python import util
from twisted import cred
from twisted.spread import pb
from twisted.spread.flavors import Referenceable
from twisted.internet import defer
from twisted.internet.defer import Deferred, DeferredQueue, DeferredList
from twisted.internet.error import ConnectionRefusedError
from twisted.internet import reactor, inotify
from twisted.internet.task import deferLater, cooperate

from twisted.application.service import Application
from twisted.application.internet import TCPClient

from twisted.python import log
from twisted.python.filepath import FilePath

from utils import ConsumerQueue, TransferPager

from backtrac.apps.catalog.utils import normpath

class ClientError(Exception): pass

class BackupJob(object):
    CREATE = 0
    MODIFY = 1
    DELETE = 2

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
        if job.type == BackupJob.CREATE and job.filepath.isdir():
            if job.filepath.exists():
                self.client.broker.create_item(path, 'd')
        elif job.type == BackupJob.MODIFY:
            try:
                mtime = job.filepath.getModificationTime()
                size = job.filepath.getsize()
                d = self.client.broker.check_file(path, mtime, size)
                d.addCallback(self._check_result, path)
            except (OSError, IOError):
                pass
        elif job.type == BackupJob.DELETE:
            print '%s deleted' % path
            self.client.broker.delete_item(path)

    def error(self, fail):
        print fail

    def _check_result(self, backup_required, path):
        if backup_required:
            self.client.transfer_queue.add(FilePath(path))

class TransferQueue(BackupQueue):
    def consume(self, filepath):
        try:
            mtime = filepath.getModificationTime()
            size = filepath.getsize()
        except (OSError, IOError):
            return
        d = self.client.broker.put_file(filepath.path, mtime, size)
        d.addCallback(self._transfer, filepath)

    def error(self, fail):
        print fail

    def _transfer(self, collector, filepath):
        try:
            pager = TransferPager(collector, filepath)
            pager.wait()
            print '%s, %d bytes' % (filepath.path, filepath.getsize())
        except (OSError, IOError):
            pass

class BackupBroker(pb.Referenceable):
    def __init__(self, server='localhost', port=8123,
                 hostname=socket.gethostname(), secret_key=''):
        self.server = server
        self.port = port
        self.hostname = hostname
        self.secret_key = secret_key
        self.connected = False
        self.factory = pb.PBClientFactory()
        self.service = TCPClient(self.hostname, self.port, self.factory)

    def get_paths(self):
        return self.perspective.callRemote('get_paths')

    def get_present_state(self, path):
        return self.perspective.callRemote('get_present_state', path)

    def check_file(self, path, mtime, size):
        return self.perspective.callRemote('check_file', path, mtime, size)

    def delete_item(self, path):
        return self.perspective.callRemote('delete_item', path)

    def create_item(self, path, type='f'):
        return self.perspective.callRemote('create_item', path, type)

    def put_file(self, path, mtime, size):
        return self.perspective.callRemote('put_file', path, mtime, size)

    def login(self):
        return self.factory.login(
            cred.credentials.UsernamePassword(
                self.hostname,
                self.secret_key
            ),
            client=self
        )

    def connect(self):
        self.service.startService()
        d = Deferred()
        r = self.login()
        r.addCallbacks(self._logged_in, self._error)
        r.addCallback(lambda _: d.callback(self))
        return d

    def _logged_in(self, perspective):
        self.perspective = perspective
        self.connected = True

    def _error(self, error):
        raise error
        if error.type == 'twisted.cred.error.UnauthorizedLogin':
            print >>sys.stderr, 'Failed to authenticate with server: %s' % self.server
        elif error.type == ConnectionRefusedError:
            print >>sys.stderr, 'Connection refused when connecting to server: %s' % self.server
        else:
            print >>sys.stderr, error.getTraceback()
        reactor.stop()

class BackupClient(object):
    def __init__(self, broker):
        self.broker = broker
        self.notifier = inotify.INotify()
        self.backup_queue = BackupQueue(self)
        self.transfer_queue = TransferQueue(self)

    @defer.inlineCallbacks
    def check_present_state(self, path):
        state = yield self.broker.get_present_state(path)
        for path in state:
            if not os.path.exists(path):
                job = BackupJob(path, type=BackupJob.DELETE)
                self.backup_queue.add(job)

    def handle_fs_event(self, watch, filepath, mask):
        def add_to_queue(job):
            self.backup_queue.add(job)
        if mask & inotify.IN_CREATE:
            type = BackupJob.CREATE
        elif mask & inotify.IN_CHANGED or mask & inotify.IN_MOVED_TO:
            type = BackupJob.MODIFY
        elif mask & inotify.IN_DELETE or mask & inotify.IN_MOVED_FROM:
            type = BackupJob.DELETE
        else:
            return
        job = BackupJob(filepath, type=type)
        reactor.callLater(1, add_to_queue, job)

    def add_watch(self, path):
        self.notifier.watch(FilePath(path), autoAdd=True,
                            recursive=True,
                            callbacks=[self.handle_fs_event])

    def walk_path(self, path):
        for root, dirs, files in os.walk(path):
            self.backup_queue.add(BackupJob(root, type=BackupJob.CREATE))
            for f in files:
                path = os.path.join(root, f)
                self.backup_queue.add(BackupJob(path))

    @defer.inlineCallbacks
    def start(self):
        self.backup_queue.start()
        self.transfer_queue.start()
        paths = yield self.broker.get_paths()
        for path in paths:
            path = normpath(path)
            state = yield self.broker.get_present_state(path)
            self.check_present_state(state)
            self.walk_path(path)
            self.add_watch(path)
        self.notifier.startReading()

if __name__ == '__main__':
    def makeClient(broker):
        BackupClient(broker).start()
    broker = BackupBroker(server='localhost', secret_key='password')
    broker.connect().addCallback(makeClient)
