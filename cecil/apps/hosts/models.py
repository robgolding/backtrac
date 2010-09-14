import datetime

from django.db import models

class Host(models.Model):
	hostname = models.CharField(max_length=255, unique=True, db_index=True)
	secret_key = models.CharField(max_length=255)
	
	@models.permalink
	def get_absolute_url(self):
		return ('hosts_host_detail', [self.id])
	
	def is_backing_up(self):
		return any([ not r.is_finished() for r in self.results.all()])
	
	def get_last_completed_result(self):
		Result = models.get_model('backups', 'Result')
		try:
			return Result.objects.filter(client=self, finished_at__isnull=False).latest()
		except Result.DoesNotExist:
			return None
	
	def get_last_result_status(self):
		result = self.get_last_completed_result()
		if not result:
			return 'N/A'
		if result.successful:
			return 'success'
		return 'error'
	
	def get_next_backup(self):
		next = None
		for backup in self.backups.active():
			if next is not None:
				r = backup.next_run()
				if r and r > next.next_run():
					next = backup
			else:
				next = backup
		return next
	
	def get_status(self):
		if self.is_backing_up():
			return 'backup running'
		cs = self.checkins.order_by('-created')
		if not cs or (cs[0].created < datetime.datetime.now() - datetime.timedelta(seconds=60)):
			return 'offline'
		return 'online'
			
	
	def __unicode__(self):
		return self.hostname
	
	class Meta:
		ordering = ('hostname',)

class Checkin(models.Model):
	host = models.ForeignKey(Host, related_name='checkins')
	created = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s @ %s' % (self.host, self.created)
