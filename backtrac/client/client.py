import os
import sys

from twisted import cred
from twisted.spread import pb
from twisted.python import failure
from twisted.internet import defer, reactor, inotify
from twisted.python.filepath import FilePath

import utils
from broker import BackupBroker
from job import BackupJob
from queue import BackupQueue, TransferQueue

from django.conf import settings

from backtrac.apps.catalog.utils import normpath

class ClientError(Exception): pass

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

def get_server_status():
    broker = BackupBroker(server='localhost', secret_key=settings.SECRET_KEY,
                          hostname='localhost')
    d = broker.connect()

    try:
        result = utils.get_result_blocking(d)
    except utils.TimoutExpiredException:
        result = False

    if isinstance(result, failure.Failure):
        return False
    return bool(d.result)

if __name__ == '__main__':
    def makeClient(broker):
        BackupClient(broker).start()
    broker = BackupBroker(server='localhost', secret_key='password')
    broker.connect().addCallback(makeClient)
