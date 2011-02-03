from twisted.internet.defer import Deferred, DeferredQueue, DeferredList
from twisted.python.filepath import FilePath

from utils import TransferPager
from job import BackupJob

class ConsumerQueue(object):
    def __init__(self, stop_on_error=False):
        self.stop_on_error = stop_on_error
        self.queue = DeferredQueue()

    def _consume_next(self, *args):
        self.queue.get().addCallbacks(self._consumer, self._error)

    def _consumer(self, obj):
        self.consume(obj)
        self._consume_next()

    def _error(self, fail):
        self.error(fail)
        if not self.stop_on_error:
            self._consume_next()

    def add(self, filepath):
        self.queue.put(filepath)

    def consume(self, obj):
        raise NotImplementedError
    
    def fail(self, fail):
        raise NotImplementedError

    def start(self):
        self._consume_next()

class BackupQueue(ConsumerQueue):
    def __init__(self, client, *args, **kwargs):
        super(BackupQueue, self).__init__(*args, **kwargs)
        self.client = client

    def consume(self, job):
        path = job.filepath.path
        if job.type == BackupJob.CREATE and job.filepath.isdir():
            if job.filepath.exists():
                self.client.broker.create_item(path, 'd')
        elif job.type == BackupJob.UPDATE:
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


