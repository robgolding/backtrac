import uuid

from django.db import models

class File(models.Model):
    client = models.ForeignKey('clients.Client', related_name='files')
    path = models.CharField(max_length=255)

    def __unicode__(self):
        return self.path

class FileVersion(models.Model):
    uuid = models.CharField(max_length=36)
    file = models.ForeignKey(File, related_name='versions')
    backed_up_at = models.DateTimeField(auto_now_add=True)
    mtime = models.IntegerField()
    size = models.BigIntegerField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.uuid = uuid.uuid4()
        super(FileVersion, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s [%s]' % (self.file.path, self.backed_up_at)
