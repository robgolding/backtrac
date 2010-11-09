from django.db import models

class Directory(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True)
    name = models.CharField(max_length=255)

    def _get_path(self):
        if self.parent is not None:
            return self.parent.path + self.name + '/'
        return '/%s/' % self.name
    path = property(_get_path)

    def __unicode__(self):
        return self.path

    class Meta:
        verbose_name_plural = 'directories'

class File(models.Model):
    client = models.ForeignKey('clients.Client', related_name='files')
    directory = models.ForeignKey(Directory, null=True, blank=True)
    name = models.CharField(max_length=255)

    def _get_path(self):
        if self.directory is not None:
            return self.directory.path + self.name
        return '/%s' % self.name
    path = property(_get_path)

    def __unicode__(self):
        return self.path

class FileVersion(models.Model):
    id = models.CharField('ID', max_length=36, primary_key=True)
    file = models.ForeignKey(File, related_name='versions')
    backed_up_at = models.DateTimeField(auto_now_add=True)
    mtime = models.IntegerField('Modified time')
    size = models.BigIntegerField()

    class Meta:
        get_latest_by = 'backed_up_at'

    def __unicode__(self):
        return '%s [%s]' % (self.file.path, self.backed_up_at)
