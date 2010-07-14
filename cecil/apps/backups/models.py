from django.db import models
from django.db.models.signals import post_save

from cecil.apps.schedules.models import Schedule, Rule
from cecil.apps.hosts.models import Host

import tasks

class Backup(models.Model):
	"""
	Model to represent a backup task, which can be either active or inactive.
	Stores the celery task_id, to keep a reference to the task which will
	execute this backup next.
	"""
	name = models.CharField(max_length=200, unique=True)
	client = models.ForeignKey(Host, related_name='backups')
	active = models.BooleanField(default=True, editable=False)
	schedule = models.ForeignKey(Schedule, related_name='backups')
	task_id = models.CharField(max_length=36, null=True, editable=False)
	
	def save(self, resubmit=True, *args, **kwargs):
		super(Backup, self).save(*args, **kwargs)
		if resubmit:
			tasks.resubmit_backup(self)
	
	@models.permalink
	def get_absolute_url(self):
		return ('backups_backup_detail', [self.id])
	
	def is_running(self):
		try:
			return not self.runs.latest().is_finished()
		except Run.DoesNotExist:
			return False
	
	def get_status(self):
		if not self.active:
			return 'paused'
		elif self.is_running():
			return 'running'
		else:
			return 'idle'
	get_status.short_description = 'Status'
	
	def next_run(self):
		return self.schedule.get_next_occurrence()
	
	def __unicode__(self):
		return self.name

class Job(models.Model):
	backup = models.ForeignKey(Backup, related_name='jobs')
	path = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.path

class Run(models.Model):
	backup = models.ForeignKey(Backup, related_name='runs')
	successful = models.BooleanField()
	started_at = models.DateTimeField(auto_now_add=True)
	finished_at = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return '%s (%s)' % (self.backup.name, self.started_at)
	
	def is_finished(self):
		return self.finished_at is None
	
	class Meta:
		get_latest_by = 'started_at'
	

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
