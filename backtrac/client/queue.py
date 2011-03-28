from twisted.internet.defer import Deferred, DeferredQueue
from twisted.python.filepath import FilePath

from backtrac.utils.transfer import TransferPager
from backtrac.client.job import BackupJob

QUEUE_TIMEOUT_SECONDS = 120

class ConsumerQueue(object):
    def __init__(self, stop_on_error=False):
        self.stop_on_error = stop_on_error
        self.queue = DeferredQueue()
        self.size = 0

    def _consume_next(self, *args):
        self.size -= 1
        self.queue.get().addCallbacks(self._consumer, self._error)

    def _consumer(self, item):
        r = self.consume(item)
        if isinstance(r, Deferred):
            r.addCallbacks(self._consume_next, self._consume_next)
        else:
            self._consume_next()

    def _error(self, fail):
        self.error(fail)
        if not self.stop_on_error:
            self._consume_next()

    def add(self, item):
        self.size += 1
        self.queue.put(item)

    def consume(self, item):
        raise NotImplementedError

    def fail(self, fail):
        raise NotImplementedError

    def start(self):
        self._consume_next()

class BackupQueue(ConsumerQueue):
    def __init__(self, client, *args, **kwargs):
        super(BackupQueue, self).__init__(*args, **kwargs)
        self.client = client

    def consume_create(self, filepath):
        # don't do anything if a file is created, as the server handles this as
        # an 'update'
        if filepath.isdir():
            return self.client.broker.create_item(filepath.path, 'd')

    def consume_update(self, filepath):
        try:
            attrs = {
                'mtime': filepath.getModificationTime(),
                'size': filepath.getsize(),
            }
            d = self.client.broker.check_file(filepath.path, attrs)
            d.addCallback(self._check_result, filepath.path)
            return d
        except (OSError, IOError):
            pass

    def consume_delete(self, filepath):
        print '%s deleted' % filepath.path
        return self.client.broker.delete_item(filepath.path)

    def consume(self, job):
        if job.type == BackupJob.CREATE:
            return self.consume_create(job.filepath)
        elif job.type == BackupJob.UPDATE:
            return self.consume_update(job.filepath)
        elif job.type == BackupJob.DELETE:
            return self.consume_delete(job.filepath)

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
        d = Deferred()
        self.client.broker.put_file(filepath.path, mtime, size).addCallback(
            self._transfer, filepath, d
        )
        return d

    def error(self, fail):
        print fail

    def _transfer(self, collector, filepath, d=None):
        try:
            fd = open(filepath.path, 'rb')
            pager = TransferPager(collector, fd)
            if d is not None:
                pager.wait().chainDeferred(d)
            print '%s, %d bytes' % (filepath.path, filepath.getsize())
        except (OSError, IOError):
            pass

class QueueManager(object):
    def __init__(self, queues):
        self.queues = queues

    def add(self, item):
        queue = min(self.queues, key=lambda q:q.size)
        queue.add(item)

    def start(self):
        for queue in self.queues:
            queue.start()

    def get_size(self):
        return sum([ queue.size for queue in self.queues ])
