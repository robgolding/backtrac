from django.db import models
from django.db.models.signals import pre_delete

from cecil.apps.schedules.models import Schedule, Rule
from cecil.apps.hosts.models import Host

from managers import BackupManager, ResultManager
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
	
	objects = BackupManager()
	
	@models.permalink
	def get_absolute_url(self):
		return ('backups_backup_detail', [self.id])
	
	def is_running(self):
		try:
			return not self.results.latest().is_finished()
		except Result.DoesNotExist:
			return False
	
	def get_status(self):
		if not self.active:
			return 'paused'
		elif self.is_running():
			return 'running'
		else:
			return 'idle'
	get_status.short_description = 'Status'
	
	def get_last_completed_result(self):
		try:
			return self.results.filter(finished_at__isnull=False).latest()
		except Result.DoesNotExist:
			return None
	
	def get_last_result_status(self):
		if self.is_running():
			results = self.results.exclude(pk=self.results.latest().pk)
		else:
			results = self.results.all()
		if not results:
			return 'N/A'
		result = results.latest()
		return result.get_status()
	
	def next_run(self):
		if not self.active:
			return None
		return self.schedule.get_next_occurrence()
	
	def resubmit(self):
		return tasks.resubmit_backup(self)
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('name',)

class Job(models.Model):
	backup = models.ForeignKey(Backup, related_name='jobs')
	path = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.path

class Result(models.Model):
	backup = models.ForeignKey(Backup, related_name='results')
	client = models.ForeignKey(Host, related_name='results')
	successful = models.BooleanField()
	started_at = models.DateTimeField(auto_now_add=True)
	finished_at = models.DateTimeField(null=True, blank=True)
	
	objects = ResultManager()
	
	@models.permalink
	def get_absolute_url(self):
		return ('backups_result_detail', [self.backup.id, self.id])
	
	def is_finished(self):
		return self.finished_at is not None
	
	def get_status(self):
		if not self.finished_at:
			return 'running'
		if self.successful:
			return 'success'
		else:
			return 'error'
	
	def __unicode__(self):
		return '%s (%s)' % (self.backup.name, self.started_at)
	
	class Meta:
		ordering = ('-started_at',)
		get_latest_by = 'started_at'

def resubmit_backup(sender, instance, **kwargs):
	if sender == Backup:
		tasks.resubmit_backup(instance)

pre_delete.connect(resubmit_backup)
