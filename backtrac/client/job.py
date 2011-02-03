from twisted.python.filepath import FilePath

class BackupJob(object):
    CREATE = 0
    UPDATE = 1
    DELETE = 2

    def __init__(self, filepath, type=UPDATE):
        if isinstance(filepath, basestring):
            filepath = FilePath(filepath)
        self.filepath = filepath
        self.type = type
