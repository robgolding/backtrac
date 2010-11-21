from django.db import models

class Client(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    secret_key = models.CharField(max_length=255)
    active = models.BooleanField(default=True, editable=False)

    @models.permalink
    def get_absolute_url(self):
        return ('clients_client_detail', [self.id])

    def get_last_modified_version(self):
        from backtrac.apps.catalog.models import Version
        try:
            return Version.objects.filter(item__client=self).latest()
        except Version.DoesNotExist:
            return None

    def __unicode__(self):
        return self.hostname

    class Meta:
        ordering = ('hostname',)

class FilePath(models.Model):
    client = models.ForeignKey(Client, related_name='filepaths')
    path = models.CharField(max_length=255)

    def __unicode__(self):
        return self.path

class Status(models.Model):
    client = models.OneToOneField(Client, primary_key=True)
    last_seen = models.DateTimeField(auto_now_add=True, auto_now=True)

    def __unicode__(self):
        return '[Status] %s' % self.client
