import uuid

from django.shortcuts import get_object_or_404
from piston.handler import BaseHandler

from cecil.apps.backups.models import Backup, Job, Result
from cecil.apps.hosts.models import Host, Checkin

class CheckinHandler(BaseHandler):
	allowed_methods = ('POST',)
	
	def create(self, request):
		c = Checkin.objects.create(host=request.user)
		todo = []
		for backup in request.user.backups.all():
			if backup.is_pending():
				todo.append(backup.id)
		return {'todo': todo}

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

class BackupBeginHandler(BaseHandler):
	allowed_methods = ('GET',)
	
	def read(self, request, id):
		backup = get_object_or_404(Backup, pk=id)
		result = Result(backup=backup, client=request.user)
		result.save()
		return {'result_id': result.id}

class BackupReceiptHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request, id):
		backup = get_object_or_404(Backup, pk=id)
		
		#from receiver import PackageReceiver
		#r = PackageReceiver(str(uuid.uuid4()))
		#r.start()
		#return {'port': r.port}
		
		f = request.FILES['report']
		
		destination = open('/home/rob/Desktop/package2.tar', 'wb+')
		for chunk in f.chunks():
			destination.write(chunk)
		destination.close()
		
		return str(len(f))
	
	create = update

class JobHandler(BaseHandler):
	allowed_mathods = ('GET',)
	model = Job
	
	fields = ['path']
