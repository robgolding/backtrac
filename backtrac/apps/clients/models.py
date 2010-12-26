import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Client(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    secret_key = models.CharField(max_length=255)
    active = models.BooleanField(default=True, editable=False)

    @models.permalink
    def get_absolute_url(self):
        return ('clients_client_detail', [self.id])

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

    class Meta:
        verbose_name_plural = 'statuses'

@receiver(post_save, sender=Client)
def create_initial_status(sender, instance=None, **kwargs):
    try:
        status = instance.status
    except Status.DoesNotExist:
        Status.objects.create(client=instance, last_seen=datetime.datetime.min)
