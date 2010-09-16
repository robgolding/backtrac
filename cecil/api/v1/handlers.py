import uuid, json, tarfile

from django.shortcuts import get_object_or_404
from piston.handler import BaseHandler

from cecil.apps.backups.models import Backup, Job, Result, ResultFile
from cecil.apps.hosts.models import Host, Checkin

from receiver import PackageReceiver

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
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request, id):
		backup = get_object_or_404(Backup, pk=id)
		result = Result(backup=backup, client=request.user)
		result.save()
		return {'result_id': result.id}
	
	create = update

class BackupReceiptHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def process_result(self, tarfile_name):
		for f in self.report['deleted']:
			rf = ResultFile.objects.create(result=self.result, path=f, type='deleted')
		try:
			t = tarfile.open(tarfile_name, 'r:gz')
			members = t.getmembers()
			for member in members:
				ResultFile.objects.create(result=self.result, path=member.name, type='added')
		except tarfile.ReadError:
			pass
	
	def update(self, request, id):
		self.backup = get_object_or_404(Backup, pk=id)
		self.result = get_object_or_404(Result, backup=self.backup, finished_at=None)
		
		report_file = request.FILES['report']
		self.report = json.loads(report_file.read())
		
		r = PackageReceiver(self.result, callback=self.process_result)
		r.start()
		return {'port': r.port}
	
	create = update

class JobHandler(BaseHandler):
	allowed_mathods = ('GET',)
	model = Job
	
	fields = ['id', 'path']
