import datetime
from django.db import models
from django.db.models.signals import pre_delete

from backtrac.apps.schedules.models import Schedule, Rule
from backtrac.apps.hosts.models import Host

from managers import BackupManager, ResultManager

RESULTFILE_TYPE_CHOICES = (
	('deleted', 'Deleted'),
	('added', 'Added'),
	('error', 'Error'),
)

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
		elif self.is_pending():
			return 'pending'
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
	
	def is_pending(self):
		last = self.schedule.get_last_occurrence()
		if self.is_running() or last is None:
			return False
		r = self.get_last_completed_result()
		if r is None:
			return True # No need to do the above check I think??
		return last != self.schedule.get_last_occurrence(before=r.finished_at)
	
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

class ResultFile(models.Model):
	result = models.ForeignKey(Result, related_name='files')
	path = models.CharField(max_length=255, db_index=True)
	size = models.BigIntegerField(null=True, blank=True)
	type = models.CharField(max_length=20, db_index=True, choices=RESULTFILE_TYPE_CHOICES)
	
	def __unicode__(self):
		return '%s \'%s\'' % (self.get_type_display(), self.path)
