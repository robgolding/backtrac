from twisted.internet import reactor, abstract

class FileSystemMonitor(object):
    def __init__(self, queue):
        pass

    def add_watch(self, path, recursive=True):
        pass

    def rm_watch(self, path):
        pass

    def stop(self):
        pass
