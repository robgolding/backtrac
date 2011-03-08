import os
import shutil
import hashlib

from backtrac.utils import makedirs, generate_version_id

class StorageError(Exception): pass

class Storage(object):
    def __init__(self, root):
        self.root = root
        makedirs(self.root)

    def _hash(self, data):
        return hashlib.sha1(data).hexdigest()

    def _get_container(self, bucket, path):
        return os.path.join(self.root, bucket, self._hash(bucket))

    def get_total_bytes(self):
        stat = os.statvfs(self.root)
        return stat.f_blocks * stat.f_frsize

    def get_avail_bytes(self):
        stat = os.statvfs(self.root)
        return stat.f_bavail * stat.f_frsize

    def get_used_bytes(self):
        return self.get_total_bytes() - self.get_avail_bytes()

    def put(self, bucket, path, version_id=None):
        if version_id is None:
            version_id = generate_version_id()
        container = self._get_container(bucket, path)
        makedirs(container)
        dst = os.path.join(container, version_id)
        if os.path.exists(dst):
            raise StorageError('Version ID \'%s\' already exists for file: %s'
                               % (version_id, path))
        fd = open(dst, 'wb')
        return version_id, fd

    def get(self, bucket, path, version_id):
        container = self._get_container(bucket, path)
        if not os.path.exists(container):
            raise StorageError('Cannot find container for file: %s' % path)
        src = os.path.join(container, version_id)
        if os.path.exists(src):
            return open(src, 'rb')
        else:
            raise StorageError('Cannot find version ID \'%s\' for file: %s'
                               % (version_id, path))
