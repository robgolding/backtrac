from django.db import models

import fields, tasks

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
	interval = fields.TimedeltaField()
	active = models.BooleanField(default=True)
	task_id = models.CharField(max_length=36, null=True, blank=True, editable=False)
	
	def save(self, resubmit=False, *args, **kwargs):
		super(Backup, self).save(*args, **kwargs)
		if resubmit:
			tasks.resubmit_backup(self)
	
	def is_running(self):
		try:
			return self.events.latest().type == 'started'
		except BackupEvent.DoesNotExist:
			return False
	
	def get_status(self):
		if self.is_running():
			return 'running'
		else:
			return 'idle'
	get_status.short_description = 'Status'
	
	def __unicode__(self):
		return self.name

class BackupEvent(models.Model):
	backup = models.ForeignKey(Backup, related_name='events')
	type = models.CharField(max_length=20, choices=BACKUP_EVENT_TYPE_CHOICES)
	occured_at = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s: %s' % (self.get_type_display(), self.backup)
	
	class Meta:
		get_latest_by = 'occured_at'
