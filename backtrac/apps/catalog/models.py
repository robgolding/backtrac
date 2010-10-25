from django.db import models

class File(models.Model):
    client = models.ForeignKey('clients.Client', related_name='files')
    path = models.CharField(max_length=255)

    def __unicode__(self):
        return self.path

class FileVersion(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    file = models.ForeignKey(File, related_name='versions')
    backed_up_at = models.DateTimeField(auto_now_add=True)
    mtime = models.IntegerField()
    size = models.BigIntegerField()

    class Meta:
        get_latest_by = 'backed_up_at'

    def __unicode__(self):
        return '%s [%s]' % (self.file.path, self.backed_up_at)
