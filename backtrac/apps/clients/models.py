import re
import fnmatch
import datetime

from django.db import models
from django.db.models.signals import post_save
from django import dispatch

from backtrac.apps.catalog.models import Version

client_connected = dispatch.Signal(providing_args=['client'])
client_disconnected = dispatch.Signal(providing_args=['client'])

class Client(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    secret_key = models.CharField(max_length=255)
    active = models.BooleanField(default=True, editable=False)

    def get_latest_version(self):
        try:
            return Version.objects.filter(item__client=self).latest()
        except Version.DoesNotExist:
            return None

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

class Exclusion(models.Model):
    client = models.ForeignKey(Client, related_name='exclusions')
    glob = models.CharField(max_length=255)

    def get_regex(self):
        regex = fnmatch.translate(self.glob)
        return re.compile(regex)

    def __unicode__(self):
        return 'Exclude %s (%s)' % (self.glob, self.client.hostname)

class Status(models.Model):
    client = models.OneToOneField(Client, primary_key=True)
    connected = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        c = 'connected' if self.connected else 'disconnected'
        return '%s %s' % (self.client.hostname, c)

    class Meta:
        verbose_name_plural = 'statuses'

@dispatch.receiver(post_save, sender=Client)
def create_initial_status(sender, instance=None, **kwargs):
    try:
        status = instance.status
    except Status.DoesNotExist:
        Status.objects.create(client=instance)

@dispatch.receiver(client_connected)
def client_connected_callback(sender, client, **kwargs):
    client.status.connected = True
    client.status.save()

@dispatch.receiver(client_disconnected)
def client_disconnected_callback(sender, client, **kwargs):
    client.status.connected = False
    client.status.save()
