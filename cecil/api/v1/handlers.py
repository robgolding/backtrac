import uuid

from django.shortcuts import get_object_or_404

from piston.handler import BaseHandler
from celery.exceptions import TimeoutError

from cecil.apps.core.tasks import check_status
from cecil.apps.backups.models import Backup, Job
from cecil.apps.hosts.models import Host

class CheckStatusHandler(BaseHandler):
	allowed_methods = ('GET',)
	
	def read(self, request):
		response = {'status': True}
		result = check_status.delay()
		try:
			result.wait(timeout=5)
		except TimeoutError:
			response['status'] = False
		finally:
			return response

class BackupHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Backup
	fields = ('id', 'name', ('client', ('hostname',)), 'status', 'jobs',)
	
	@classmethod
	def next_run(cls, backup):
		return backup.next_run()
	
	@classmethod
	def status(cls, backup):
		return backup.get_status()
	
	@classmethod
	def jobs(cls, backup):
		return backup.jobs.all()

class BackupReceiptHandler(BaseHandler):
	allowed_methods = ('GET',)
	
	def read(self, request, id):
		backup = get_object_or_404(Backup, pk=id)
		
		from receiver import PackageReceiver
		r = PackageReceiver(str(uuid.uuid4()))
		r.start()
		return r.port
	
	fields = ['port']

class JobHandler(BaseHandler):
	allowed_mathods = ('GET',)
	model = Job
	
	fields = ['path']
