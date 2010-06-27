from django.db import models
from django.db.models.signals import post_save

from cecil.apps.schedules.models import Schedule, Rule
from cecil.apps.hosts.models import Host

import tasks

BACKUP_EVENT_TYPE_CHOICES = (
	('started', 'Backup started'),
	('finished', 'Backup finished'),
	('error', 'Backup error'),
)

class Backup(models.Model):
	"""
	Model to represent a backup task, which can be either active or inactive.
	Stores the celery task_id, to keep a reference to the task which will
	execute this backup next.
	"""
	name = models.CharField(max_length=200, unique=True)
	client = models.ForeignKey(Host)
	active = models.BooleanField(default=True)
	schedule = models.ForeignKey(Schedule, related_name='backups')
	task_id = models.CharField(max_length=36, null=True, editable=False)
	
	def save(self, resubmit=True, *args, **kwargs):
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

class BackupPath(models.Model):
	backup = models.ForeignKey(Backup, related_name='paths')
	path = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.path

class BackupEvent(models.Model):
	backup = models.ForeignKey(Backup, related_name='events')
	type = models.CharField(max_length=20, choices=BACKUP_EVENT_TYPE_CHOICES)
	occured_at = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s: %s' % (self.get_type_display(), self.backup)
	
	class Meta:
		get_latest_by = 'occured_at'

def resubmit_backup(sender, instance, **kwargs):
	if sender == Schedule:
		backups = instance.backups.all()
	elif sender == Rule:
		backups = instance.schedule.backups.all()
	else:
		return
	for backup in backups:
		tasks.resubmit_backup(backup)

post_save.connect(resubmit_backup)
