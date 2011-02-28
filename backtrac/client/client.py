import os
import sys

from twisted import cred
from twisted.spread import pb
from twisted.python import failure
from twisted.internet import defer, reactor
from twisted.python.filepath import FilePath

from django.conf import settings

from backtrac.client import utils
from backtrac.client.broker import BackupBroker
from backtrac.client.job import BackupJob
from backtrac.client.queue import BackupQueue, TransferQueue
from backtrac.client.platform import FileSystemMonitor
from backtrac.utils.transfer import PageCollector

from backtrac.apps.catalog.utils import normpath

class ClientError(Exception): pass

class BackupClient(pb.Referenceable):
    def __init__(self, broker):
        self.broker = broker
        self.backup_queue = BackupQueue(self)
        self.transfer_queue = TransferQueue(self)
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

    @defer.inlineCallbacks
    def start(self):
        broker = yield self.broker.connect(client=self)
        self.backup_queue.start()
        self.transfer_queue.start()
        paths = yield self.broker.get_paths()
        for path in paths:
            path = normpath(path)
            self.check_present_state(path)
            self.walk_path(path)
            self.monitor.add_watch(path)

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
