import os
import datetime

from django.conf import settings

from backtrac.apps.core.models import GlobalExclusion
from backtrac.apps.clients import models as client_models
from backtrac.apps.clients.models import client_connected, client_disconnected
from backtrac.apps.catalog.models import Item, Version, Event, RestoreJob, \
        item_created, item_updated, item_deleted
from backtrac.utils import generate_version_id

def get_client(hostname):
    try:
        client_obj = client_models.Client.objects.get(hostname=hostname)
        return Client(client_obj)
    except client_models.Client.DoesNotExist:
        return None

class Client(object):
    def __init__(self, client_obj):
        self.client_obj = client_obj

    def connected(self):
        client_connected.send(sender=self.client_obj, client=self.client_obj)

    def disconnected(self):
        client_disconnected.send(sender=self.client_obj, client=self.client_obj)

    def get_hostname(self):
        return self.client_obj.hostname

    def get_key(self):
        return self.client_obj.secret_key

    def get_paths(self):
        return [ p.path for p in self.client_obj.filepaths.all() ]

    def get_exclusions(self):
        return [ excl.glob for excl in self.client_obj.exclusions.all() ]

    def get_present_state(self, path):
        def get_children(item, items):
            items.append(item.path)
            for i in item.children.present():
                get_children(i, items)
        items = []
        try:
            item = Item.objects.get(client=self.client_obj, path=path)
            get_children(item, items)
        except Item.DoesNotExist:
            pass
        return items

    def is_excluded(self, path):
        _, basename = os.path.split(path)
        exclusions = list(self.client_obj.exclusions.all()) + \
                list(GlobalExclusion.objects.all())

        return any([ e.get_regex().match(basename) for e in exclusions ])

    def create_item(self, path, type):
        item_created.send(sender=self.client_obj, path=path, type=type,
                          client=self.client_obj)

    def update_item(self, path, mtime, size, version_id):
        item_updated.send(sender=self.client_obj, path=path, mtime=mtime,
                          size=size, client=self.client_obj,
                          version_id=version_id)

    def delete_item(self, path):
        item_deleted.send(sender=self.client_obj, path=path,
                          client=self.client_obj)

    def backup_required(self, path, mtime, size):
        try:
            item = Item.objects.get(client=self.client_obj, path=path)
            if not item.latest_version or item.deleted:
                return True
            if abs(size - item.latest_version.size) < 1:
                if item.latest_version.is_restored() or \
                   abs(mtime - item.latest_version.mtime) < 1:
                    return False
        except Item.DoesNotExist:
            pass
        return True

    def get_pending_restore_jobs(self):
        jobs = self.client_obj.restores.filter(started_at=None,
                                               completed_at=None)
        result = []
        for job in jobs:
            # resolve the original version, to get the correct version ID for
            # pulling out of the storage subsystem
            version = job.version.resolve_original()
            result.append((
                    job.id,
                    job.version.item.path,
                    version.id,
                    job.destination_path,
            ))
        return result

    def restore_begin(self, restore_id):
        try:
            # set the start time of the restore job so we know it's in progress
            job = RestoreJob.objects.get(id=restore_id)
            job.started_at = datetime.datetime.now()
            job.save()
        except RestoreJob.DoesNotExist:
            pass

    def restore_complete(self, restore_id):
        try:
            # set the completion time of the restore job so we know it's done
            job = RestoreJob.objects.get(id=restore_id)
            job.completed_at = datetime.datetime.now()
            job.save()
            # copy the version to the latest slot so the restored file is not
            # backed up again, generating a brand new ID and setting the
            # restored_from value to the original version for later use
            version = job.version
            restored = Version.objects.create(id=generate_version_id(),
                                              item=version.item,
                                              mtime=version.mtime,
                                              size=version.size,
                                              restored_from=version)
            # make sure the item isn't marked as deleted any more
            version.item.deleted = False
            version.item.save()
            # create an event for the restore
            Event.objects.create(type='restored', item=version.item)
        except RestoreJob.DoesNotExist:
            pass
