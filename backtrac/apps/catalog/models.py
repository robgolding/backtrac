from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

ITEM_TYPE_CHOICES = (
    ('d', 'Directory'),
    ('f', 'File'),
)

def get_or_create_item(client, path, type):
    names = path.strip('/').split('/')
    item, created = None, False
    types = ['f' if i == (len(names) - 1) else 'd' for i in range(len(names))]
    for name, type in zip(names, types):
        item, created = Item.objects.get_or_create(client=client,
                                                   parent=item,
                                                   name=name,
                                                   type=type)
    return item, created

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
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    deleted = models.BooleanField(default=False, db_index=True)

    def _get_path(self):
        if self.parent is not None:
            return '%s/%s' % (self.parent.path, self.name)
        return '/' + self.name

    def _is_deleted(self):
        if self.latest_version:
            if self.deleted_at:
                return self.deleted_at > self.latest_version.backed_up_at
            return False
        return bool(self.deleted_at)

    @models.permalink
    def get_absolute_url(self):
        return ('catalog_browse_route', [self.client.id, self.path[1:]])

    def __unicode__(self):
        return self.path

class Version(models.Model):
    id = models.CharField('ID', max_length=36, primary_key=True)
    item = models.ForeignKey(Item, related_name='versions', db_index=True)
    backed_up_at = models.DateTimeField(auto_now_add=True, db_index=True)
    mtime = models.IntegerField('Modified time')
    size = models.BigIntegerField()

    class Meta:
        get_latest_by = 'backed_up_at'

    def __unicode__(self):
        return '%s [%s]' % (self.item.path, self.backed_up_at)

@receiver(pre_save, sender=Item)
def update_item(sender, instance=None, **kwargs):
    instance.path = instance._get_path()
    instance.deleted = instance._is_deleted()

@receiver(post_save, sender=Item)
def update_children(sender, instance=None, **kwargs):
    children = Item.objects.filter(parent=instance)
    for item in children:
        item.save()

@receiver(post_save, sender=Version)
def update_latest_version(sender, instance=None, **kwargs):
    instance.item.latest_version = instance
    instance.item.save()
