import os, re, shutil, tarfile

from django.conf import settings
from django.utils.datastructures import SortedDict
from django.db.models import get_model

Backup = get_model('backups', 'Backup')
BackedUpFile = get_model('backups', 'BackedUpFile')

class StorageException(Exception): pass

class Package(object):

    def __init__(self, storage, backup, filename):
        self.storage = storage
        self.backup = backup
        self.filename = filename

        if not os.path.exists(self.filename):
            raise StorageException('Cannot instantiate a Package object for %s: file does not exist' % self.filename)

    def mergewith(self, package):
        try:
            base_tarfile = tarfile.open(self.filename, 'r:gz')
        except tarfile.ReadError:
            os.remove(base)
            return

class Storage(object):
    RE_PACKAGES = re.compile('[0-9]{12}\.(\S{36})\.(tar|tar\.gz)$')

    def __init__(self, root):
        self.root = root
        if not os.path.exists(self.root):
            os.makedirs(self.root)

    def _merge(self, base, diff, delete_old=True):
        print 'merging %s with %s' % (base, diff)
        try:
            base_tarfile = tarfile.open(base, 'r:gz')
        except tarfile.ReadError:
            if delete_old:
                os.remove(base)
            return
        skip_diff = False
        try:
            diff_tarfile = tarfile.open(diff, 'r:gz')
        except tarfile.ReadError:
            skip_diff = True
        uuid = re.search(self.RE_PACKAGES, os.path.split(base)[1]).group(1)
        temp_tarfile = tarfile.open(os.path.join(settings.BACKTRAC_TMP_DIR, '%s.tar.gz' % uuid), 'w:gz')

        try:
            backup = Backup.objects.get(uuid=uuid)
            deleted = [ f.path for f in BackedUpFile.objects.filter(backup=backup, action='deleted') ]
            for member in base_tarfile.getmembers():
                if member.name not in deleted:
                    temp_tarfile.addfile(member)
            if not skip_diff:
                for member in diff_tarfile.getmembers():
                    temp_tarfile.addfile(member)
                diff_tarfile.close()
            base_tarfile.close()
            temp_tarfile.close()
            shutil.move(temp_tarfile.name, diff)
            if delete_old:
                os.remove(base)
        except Backup.DoesNotExist:
            raise StorageException('Cannot find Backup object with UUID \'%s\'' % uuid)
        print 'done merging'

    def add_package(self, backup, package):
        client_path = os.path.join(self.root, backup.client.hostname)
        filename = '%s.%s.tar.gz' % (backup.started_at.strftime('%Y%m%d%H%M'), backup.uuid)
        if not os.path.exists(client_path):
            os.makedirs(client_path)
        path = os.path.join(client_path, filename)
        contents = os.listdir(client_path)
        packages = filter(self.RE_PACKAGES.match, contents)
        backups = { }
        for p in packages:
            uuid = re.search(self.RE_PACKAGES, p).group(1)
            backups[uuid] = os.path.abspath(os.path.join(client_path, p))
        qs = Backup.objects.filter(uuid__in=backups.keys()).order_by('-finished_at')
        bs = []
        for b in qs:
            bs.append(backups[b.uuid])
        while len(bs) > 1 and len(bs) > 2 - 1: #TODO: change this hardcoded value to a history field on backup.client
            self._merge(bs[-1], bs[-2])
            del bs[-1]
        shutil.move(package, path)
