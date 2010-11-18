from django.db import models

ITEM_TYPE_CHOICES = (
    ('d', 'Directory'),
    ('f', 'File'),
)

class Item(models.Model):
    client = models.ForeignKey('clients.Client', related_name='items')
    parent = models.ForeignKey('self', null=True, blank=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=2, choices=ITEM_TYPE_CHOICES)

    def get_name(self):
        if self.type == 'f':
            return self.name
        if self.type == 'd':
            return self.name + '/'

    def _get_path(self):
        if self.parent is not None:
            return self.parent.path + self.get_name()
        return '/' + self.get_name()
    path = property(_get_path)

    @models.permalink
    def get_absolute_url(self):
        return ('catalog_browse_client', [self.client.id, self.get_name()])

    def __unicode__(self):
        return self.path

class Version(models.Model):
    id = models.CharField('ID', max_length=36, primary_key=True)
    item = models.ForeignKey(Item, related_name='versions')
    backed_up_at = models.DateTimeField(auto_now_add=True)
    mtime = models.IntegerField('Modified time')
    size = models.BigIntegerField()

    class Meta:
        get_latest_by = 'backed_up_at'

    def __unicode__(self):
        return '%s [%s]' % (self.item.path, self.backed_up_at)
