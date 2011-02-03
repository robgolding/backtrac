import pyinotify

from twisted.internet import reactor, abstract

from backtrac.client.job import BackupJob

RELEVANT_INOTIFY_EVENTS = (
    pyinotify.IN_CLOSE_NOWRITE |
    pyinotify.IN_CLOSE_WRITE |
    pyinotify.IN_CREATE |
    pyinotify.IN_DELETE |
    pyinotify.IN_MOVED_FROM |
    pyinotify.IN_MOVED_TO
)

class EventProcessor(pyinotify.ProcessEvent):
    def __init__(self, monitor):
        self.monitor = monitor

    def _file_created(self, path):
        job = BackupJob(path, type=BackupJob.CREATE)
        self.monitor.queue.add(job)

    def _file_updated(self, path):
        job = BackupJob(path, type=BackupJob.UPDATE)
        self.monitor.queue.add(job)

    def _file_deleted(self, path):
        job = BackupJob(path, type=BackupJob.DELETE)
        self.monitor.queue.add(job)

    def process_IN_CREATE(self, event):
        print 'File created:', event.pathname
        self._file_created(event.pathname)

    def process_IN_MOVED_TO(self, event):
        print 'File moved to:', event.pathname
        self._file_created(event.pathname)

    def process_IN_CLOSE_WRITE(self, event):
        print 'File written:', event.pathname
        self._file_updated(event.pathname)

    def process_IN_DELETE(self, event):
        print 'File deleted:', event.pathname
        self._file_deleted(event.pathname)

    def process_IN_MOVED_FROM(self, event):
        print 'File moved from:', event.pathname
        self._file_deleted(event.pathname)

class FileSystemMonitor(object):
    def __init__(self, queue):
        self.queue = queue
        self.wm = pyinotify.WatchManager()
        self.processor = EventProcessor(self)
        self.notifier = pyinotify.Notifier(self.wm, self.processor)
        self._reader = self._hook_into_twisted(self.wm, self.notifier)
        self.w_dict = {}

    def add_watch(self, path, recursive=True):
        mask = RELEVANT_INOTIFY_EVENTS
        result = self.wm.add_watch(path, mask, rec=recursive, auto_add=True)
        self.w_dict[path] = result[path]

    def rm_watch(self, path):
        if not self.w_dict.hasattr(path):
            return
        wd = self.w_dict.pop(path)
        self.wm.rm_watch(wd)

    def _hook_into_twisted(self, wm, notifier):
        class Reader(abstract.FileDescriptor):
            def fileno(self):
                return wm._fd

            def doRead(self):
                notifier.read_events()
                notifier.process_events()

        reader = Reader()
        reactor.addReader(reader)
        return reader

    def stop(self):
        self.notifier.stop()
        reactor.removeReader(self._reader)
