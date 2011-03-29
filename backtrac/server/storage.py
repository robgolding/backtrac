import os
import shutil
import hashlib

from backtrac.utils import makedirs, generate_version_id

class StorageError(Exception): pass

class Storage(object):
    """
    The Storage system provides a simple interface for storing and retrieving
    files, organised into buckets. Each file name can have a limitless number
    of versions, which are identified by a unique ID (i.e. a UUID).
    """
    def __init__(self, root):
        """
        Initialise the storage system by creating the root directory if it
        doesn't already exist.
        """
        self.root = root
        makedirs(self.root)

    def _hash(self, name):
        """
        Calculate a hash of the given file name, which contains only characters
        that are valid on the file system.
        """
        # encode the filename into ascii so hashlib doesn't shit the bed
        encoded = name.encode("ascii", "replace")
        return hashlib.sha1(encoded).hexdigest()

    def _get_container(self, bucket, name):
        """
        Get the container for the given file name, within the specified bucket.
        """
        return os.path.join(self.root, bucket, self._hash(name))

    def get_total_bytes(self):
        """
        Get the size of the file system on which this storage subsystem resides,
        in bytes.
        """
        stat = os.statvfs(self.root)
        return stat.f_blocks * stat.f_frsize

    def get_avail_bytes(self):
        """
        Get the number of bytes available on the file system on which this
        storage subsystem resides.
        """
        stat = os.statvfs(self.root)
        return stat.f_bavail * stat.f_frsize

    def get_used_bytes(self):
        """
        Get the number of bytes used on the file system on which this storage
        subsystem resides.
        """
        return self.get_total_bytes() - self.get_avail_bytes()

    def put(self, bucket, name, version_id=None):
        """
        Put a file into the given bucket, with the given name. If version_id is
        not specified, one will be generated automatically and the file will be
        placed under that ID.

        Returns a tuple (version_id, file_descriptor), where file_descriptor is
        opened in write (bytes) mode. Be sure to close() this once finished
        writing.
        """
        if version_id is None:
            version_id = generate_version_id()
        container = self._get_container(bucket, name)
        makedirs(container)
        dst = os.path.join(container, version_id)
        if os.path.exists(dst):
            raise StorageError('Version ID \'%s\' already exists for file: %s'
                               % (version_id, name))
        fd = open(dst, 'wb')
        return version_id, fd

    def get(self, bucket, name, version_id):
        """
        Retrieve a file with the given name and version ID, from the specified
        bucket.

        Returns a file descriptor opened in read (bytes) mode. Be sure to
        close() this when finished with the file.
        """
        container = self._get_container(bucket, name)
        if not os.path.exists(container):
            raise StorageError('Cannot find container for file: %s' % name)
        src = os.path.join(container, version_id)
        if os.path.exists(src):
            return open(src, 'rb')
        else:
            raise StorageError('Cannot find version ID \'%s\' for file: %s'
                               % (version_id, name))
