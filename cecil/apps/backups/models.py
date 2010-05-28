from django.db import models

from cecil.apps.events.models import Event

class Backup(models.Model):
	name = models.CharField(max_length=200, unique=True)
	host = models.CharField(max_length=200)
	directory = models.CharField(max_length=255)
	next_run = models.DateTimeField()
	interval = models.BigIntegerField()
	active = models.BooleanField(default=True)
	
	def __unicode__(self):
		return self.name
