import datetime
from django.db import models

from cecil.apps.schedules.models import Schedule, Rule

class Client(models.Model):
	hostname = models.CharField(max_length=255, unique=True, db_index=True)
	secret_key = models.CharField(max_length=255)
	schedule = models.ForeignKey(Schedule, related_name='clients')
	active = models.BooleanField(default=True, editable=False)
	
	@models.permalink
	def get_absolute_url(self):
		return ('clients_client_detail', [self.id])
	
	def is_backing_up(self):
		return any([ not b.is_finished() for b in self.backups.all()])
	
	def get_schedule(self):
		return self.schedule #TODO:or system schedule
	
	def get_last_completed_backup(self):
		Backup = models.get_model('backups', 'Backup')
		try:
			return Backup.objects.filter(client=self, finished_at__isnull=False).latest()
		except Backup.DoesNotExist:
			return None
	
	def get_last_backup_status(self):
		backup = self.get_last_completed_backup()
		if not backup:
			return 'N/A'
		if backup.successful:
			return 'success'
		return 'error'
	
	def get_status(self):
		if self.is_backing_up():
			return 'backup running'
		if self.backup_pending():
			return 'backup pending'
		cs = self.checkins.order_by('-created')
		if not cs or (cs[0].created < datetime.datetime.now() - datetime.timedelta(seconds=60)):
			return 'offline'
		return 'online'
	
	def next_run(self):
		if not self.active:
			return None
		return self.get_schedule().get_next_occurrence()
	
	def backup_pending(self):
		last = self.get_schedule().get_last_occurrence()
		if self.is_backing_up() or last is None:
			return False
		b = self.get_last_completed_backup()
		if b is None:
			return True
		return last != self.schedule.get_last_occurrence(before=b.finished_at)
	
	def __unicode__(self):
		return self.hostname
	
	class Meta:
		ordering = ('hostname',)

class FilePath(models.Model):
	client = models.ForeignKey(Client, related_name='filepaths')
	path = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.path

class Checkin(models.Model):
	client = models.ForeignKey(Client, related_name='checkins')
	created = models.DateTimeField(auto_now_add=True, auto_now=True)
	
	def __unicode__(self):
		return '%s @ %s' % (self.client, self.created)
