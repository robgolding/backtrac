from django.db import models

from cecil.apps.events.models import Event

BACKUP_EVENT_TYPE_CHOICES = (
	('started', 'Backup started'),
	('finished', 'Backup finished'),
	('error', 'Backup error'),
)

class Backup(models.Model):
	name = models.CharField(max_length=200, unique=True)
	host = models.CharField(max_length=200)
	directory = models.CharField(max_length=255)
	next_run = models.DateTimeField()
	interval = models.BigIntegerField()
	active = models.BooleanField(default=True)
	task_id = models.CharField(max_length=36, null=True, blank=True, editable=False)
	
	def __unicode__(self):
		return self.name

class BackupEvent(models.Model):
	backup = models.ForeignKey(Backup)
	type = models.CharField(max_length=20, choices=BACKUP_EVENT_TYPE_CHOICES)
	occured_at = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s: %s' % (self.get_type_display(), self.backup)
