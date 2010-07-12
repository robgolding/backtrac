from piston.handler import BaseHandler

from cecil.apps.backups.models import Backup, Job
from cecil.apps.hosts.models import Host

class TodoHandler(BaseHandler):
	allowed_methods = ('GET',)
	
	def read(self, request):
		host = request.user
		todo = []
		for backup in host.backups.all():
			if backup.is_pending():
				todo.append(backup)
		
		return todo

class BackupHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Backup
	
	@classmethod
	def next_run(cls, backup):
		return backup.next_run()
	
	@classmethod
	def status(cls, backup):
		return backup.get_status()
	
	@classmethod
	def jobs(cls, backup):
		return backup.jobs.all()
	
	fields = ['id', 'name', 'client', 'status', 'jobs', 'next_run']

class HostHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Host
	
	fields = ['hostname']

class JobHandler(BaseHandler):
	allowed_mathods = ('GET',)
	model = Job
	
	fields = ['path']
