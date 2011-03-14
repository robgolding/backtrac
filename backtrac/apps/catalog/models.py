import os
import datetime

from django.db import models, IntegrityError
from django.db.models.signals import pre_save, post_save
from django.utils.encoding import filepath_to_uri
from django import dispatch

from backtrac.apps.catalog import managers

item_created = dispatch.Signal(providing_args=['path', 'type'])
item_updated = dispatch.Signal(
                        providing_args=['path', 'mtime', 'size', 'client'])
item_deleted = dispatch.Signal(providing_args=['path', 'client'])

ITEM_TYPE_CHOICES = (
    ('d', 'Directory'),
    ('f', 'File'),
)

EVENT_TYPE_CHOICES = (
    ('created', 'Created'),
    ('updated', 'Updated'),
    ('deleted', 'Deleted'),
    ('restored', 'Restored'),
)

def get_or_create_item(client, path, type):
    if path == '/':
        return None, False
    path = path.rstrip('/')
    head, tail = os.path.split(path)
    parent, created = get_or_create_item(client, head, 'd')
    return Item.objects.get_or_create(client=client, name=tail, type=type,
                                      parent=parent)

class Item(models.Model):
    """
    An 'item' is a file or directory that has been backed up.
    """
    client = models.ForeignKey('clients.Client', related_name='items',
                               db_index=True)
    parent = models.ForeignKey('self', null=True, blank=True, db_index=True,
                               related_name='children')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=2, choices=ITEM_TYPE_CHOICES,
                            db_index=True)
    path = models.CharField(max_length=255, null=True, blank=True,
                            db_index=True)
    latest_version = models.ForeignKey('catalog.Version', null=True,
                                       blank=True, db_index=True,
                                       related_name='item_latest_set')
    deleted = models.BooleanField(default=False, db_index=True)

    objects = managers.ItemManager()

    def _get_path(self):
        if self.parent is not None:
            return '%s/%s' % (self.parent.path, self.name)
        return '/' + self.name

    @models.permalink
    def get_absolute_url(self):
        path = filepath_to_uri(self.path[1:])
        return ('catalog_browse_route', [self.client.id, path])

    def __unicode__(self):
        return self.path

    class Meta:
        ordering = ['name']
        unique_together = (
            ('client', 'path'),
            ('parent', 'name'),
        )

class Version(models.Model):
    id = models.CharField('ID', max_length=36, primary_key=True)
    item = models.ForeignKey(Item, related_name='versions', db_index=True)
    backed_up_at = models.DateTimeField(auto_now_add=True, db_index=True)
    mtime = models.IntegerField('Modified time')
    size = models.BigIntegerField()
    hash = models.CharField(max_length=36, null=True, blank=True)
    restored_from = models.ForeignKey('self', null=True, blank=True, db_index=True)

    def is_restored(self):
        return self.restored_from is not None

    def resolve_original(self):
        if self.is_restored():
            return self.restored_from.resolve_original()
        return self

    class Meta:
        get_latest_by = 'backed_up_at'
        ordering = ('-backed_up_at', '-mtime')

    def __unicode__(self):
        return '%s [%s]' % (self.item.path, self.backed_up_at)

class Event(models.Model):
    item = models.ForeignKey(Item, db_index=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES,
                            db_index=True)

    def __unicode__(self):
        return '%s %s' % (self.get_type_display(), self.item.name)

    class Meta:
        ordering = ['-occurred_at']
        get_latest_by = 'occurred_at'

class RestoreJob(models.Model):
    client = models.ForeignKey('clients.Client', related_name='restores',
                               db_index=True)
    version = models.ForeignKey(Version, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def is_pending(self):
        return self.completed_at is None and self.started_at is None

    def is_in_progress(self):
        return not self.is_pending() and not self.is_complete()

    def is_complete(self):
        return self.completed_at is not None

    def __unicode__(self):
        if self.is_pending():
            status = 'pending'
        else:
            if self.is_complete():
                status = 'complete'
            else:
                status = 'in progress'
        return 'Restore %s to %s (%s)' % (self.version, self.client, status)

@dispatch.receiver(pre_save, sender=Item)
def update_item(sender, instance=None, **kwargs):
    instance.path = instance._get_path()

@dispatch.receiver(post_save, sender=Item)
def update_children(sender, instance=None, **kwargs):
    children = Item.objects.filter(parent=instance)
    for item in children:
        item.save()

@dispatch.receiver(post_save, sender=Version)
def update_latest_version(sender, instance=None, **kwargs):
    versions = instance.item.versions.all()
    latest = versions.latest()
    instance.item.latest_version = latest
    instance.item.save()

@dispatch.receiver(item_created)
def item_created_callback(sender, path, type, client, **kwargs):
    try:
        item, created = get_or_create_item(client, path, type)
        if created or item.deleted:
            if item.deleted:
                item.deleted = False
                item.save()
            Event.objects.create(item=item, type='created')
    except IntegrityError:
        pass

@dispatch.receiver(item_updated)
def item_updated_callback(sender, path, mtime, size, client, version_id,
                          **kwargs):
    try:
        item, created = get_or_create_item(client, path, 'f')
        version, _ = Version.objects.get_or_create(id=version_id, item=item,
                                                   mtime=mtime, size=size)
        if created:
            type = 'created'
        else:
            if item.deleted:
                item.deleted = False
                item.save()
            type = 'updated'
        Event.objects.create(item=item, type=type)
    except IntegrityError:
        pass

@dispatch.receiver(item_deleted)
def item_deleted_callback(sender, path, client, **kwargs):
    try:
        item = Item.objects.get(client=client, path=path)
        item.deleted = True
        item.save()
        Event.objects.create(item=item, type='deleted')
    except Item.DoesNotExist:
        pass
