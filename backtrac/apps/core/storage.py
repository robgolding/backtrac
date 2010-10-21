import os, shutil, hashlib, uuid

from django.conf import settings
from django.utils.datastructures import SortedDict
from django.db.models import get_model

from utils import makedirs

File = get_model('catalog', 'File')
FileVersion = get_model('catalog', 'FileVersion')

class StorageError(Exception): pass

class Storage(object):
    def __init__(self, root):
        self.root = root
        makedirs(self.root)

class ClientStorage(object):
    def __init__(self, storage, client):
        self.storage = storage
        self.client = client
        self.root = os.path.join(self.storage.root, self.client.hostname)
        makedirs(self.root)

    def _hash(self, data):
        return hashlib.sha1(data).hexdigest()

    def _get_container(self, path):
        return os.path.join(self.root, self._hash(path))

    def add(self, path, source, version_id=None):
        if version_id is None:
            version_id = uuid.uuid4()
        container = self._get_container(path)
        makedirs(container)
        dst = os.path.join(container, uuid)
        if os.path.exists(dst):
            raise StorageError('Version ID \'%s\' already exists for file: %s'
                               % (version_id, path))
        destination = open(dst, 'wb')
        shutil.copyfileobj(source, destination)
        return version_id

    def get(self, path, version_id):
        container = self._get_container(path)
        if not os.path.exists(container):
            raise StorageError('Cannot find container for file: %s' % path)
        src = os.path.join(container, version_id)
        if os.path.exists(src):
            return open(src, 'rb')
        else:
            raise StorageError('Cannot find version ID \'%s\' for file: %s'
                               % (version_id, path))

