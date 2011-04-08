import os
import sys

from twisted import cred
from twisted.spread import pb
from twisted.python import failure
from twisted.internet import defer, reactor
from twisted.internet.task import LoopingCall
from twisted.python.filepath import FilePath

from django.conf import settings

from backtrac.client import utils
from backtrac.client.broker import BackupBroker
from backtrac.client.job import BackupJob
from backtrac.client.queue import BackupQueue, TransferQueue, QueueManager
from backtrac.client.platform import FileSystemMonitor
from backtrac.utils import makedirs
from backtrac.utils.transfer import PageCollector

from backtrac.apps.catalog.utils import normpath

BACKUP_QUEUE_SLOTS = 5
TRANSFER_QUEUE_SLOTS = 5

class ClientError(Exception): pass

class BackupClient(pb.Referenceable):
    def __init__(self, broker):
        self.broker = broker
        self.backup_queue = QueueManager(
            [ BackupQueue(self) for i in range(BACKUP_QUEUE_SLOTS) ]
        )
        self.transfer_queue = QueueManager(
            [ TransferQueue(self) for i in range(TRANSFER_QUEUE_SLOTS) ]
        )
        self.startup_queue = TransferQueue(self, empty=self._startup_complete)
        self.monitor = FileSystemMonitor(self.backup_queue)

    @defer.inlineCallbacks
    def check_present_state(self, path):
        state = yield self.broker.get_present_state(path)
        for path in state:
            if not os.path.exists(path):
                job = BackupJob(path, type=BackupJob.DELETE)
                self.backup_queue.add(job)

    def walk_path(self, path):
        for root, dirs, files in os.walk(path):
            self.backup_queue.add(BackupJob(root, type=BackupJob.CREATE))
            for f in files:
                path = os.path.join(root, f)
                self.backup_queue.add(BackupJob(path))

    def get_index(self, path):
        index = {}
        for root, dirs, files in os.walk(path):
            index[root] = {}
            for f in files:
                path = os.path.join(root, f)
                filepath = FilePath(path)
                try:
                    index[path] = {
                        'mtime': filepath.getModificationTime(),
                        'size': filepath.getsize(),
                    }
                except OSError:
                    # file could be a broken symlink, or deleted mid-scan
                    continue
        return index

    @defer.inlineCallbacks
    def check_index(self, path, index):
        backup = yield self.broker.check_index(path, index)
        for p in backup:
            #self.backup_queue.add(BackupJob(path))
            self.startup_queue.add(FilePath(p))
        print "Indexed %s" % path

    def remote_put_file(self, path):
        self.monitor.add_exclusion(path)
        makedirs(os.path.split(path)[0])
        fdst = open(path, 'wb')
        collector = PageCollector(fdst)
        collector.wait().addCallback(
            lambda p: reactor.callLater(1, self.monitor.rm_exclusion, p)
        )
        return collector

    @defer.inlineCallbacks
    def start(self):
        try:
            yield self.broker.connect(client=self)
            paths = yield self.broker.get_paths()
            for path in paths:
                path = normpath(path)
                self.monitor.add_watch(path)
                index = self.get_index(path)
                self.check_present_state(path)
                self.check_index(path, index)
                #self.walk_path(path)
            self.startup_queue.start()
            self.backup_queue.start()
            self.transfer_queue.start()
        except Exception, e:
            print "Connection error:", e.value.getErrorMessage()

    def _startup_complete(self):
        #self.startup_queue.stop()
        pass

def get_server_status():
    broker = BackupBroker(server='localhost', secret_key=settings.SECRET_KEY,
                          hostname='localhost')
    d = broker.connect()

    # Add an errback to redirect the failure into oblivion, so we don't get an
    # exception if the server isn't running
    d.addErrback(lambda x: None)

    try:
        result = utils.get_result_blocking(d)
    except utils.TimoutExpiredException:
        result = False

    broker.factory.disconnect()

    if isinstance(result, failure.Failure):
        return False
    return bool(d.result)
