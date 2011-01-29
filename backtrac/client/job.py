from twisted.python.filepath import FilePath

class BackupJob(object):
    CREATE = 0
    MODIFY = 1
    DELETE = 2

    def __init__(self, filepath, type=MODIFY):
        if isinstance(filepath, basestring):
            filepath = FilePath(filepath)
        self.filepath = filepath
        self.type = type
