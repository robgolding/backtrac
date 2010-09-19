import os, sys, uuid, json, tarfile

from django.shortcuts import get_object_or_404
from django.conf import settings
from piston.handler import BaseHandler

from cecil.apps.backups.models import Backup, BackedUpFile
from cecil.apps.clients.models import Client, Checkin

from receiver import PackageReceiver

class CheckinHandler(BaseHandler):
	allowed_methods = ('POST',)
	
	def create(self, request):
		c = Checkin.objects.create(host=request.user)
		return { 'pending': request.user.is_pending() }

class BeginBackupHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request):
		backup = Backup.objects.create(client=request.user)
		return {'backup_id': backup.id}
	
	create = update

class BackupReceiptHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def process_result(self, tarfile_name):
		root = os.path.join(settings.BACKTRAC_BACKUP_ROOT, 'backup-%d' % self.result.backup.id)
		try:
			t = tarfile.open(tarfile_name, 'r:gz')
			members = t.getmembers()
			for member in members:
				t.extract(member, path=root)
				extracted = os.path.join(root, member.name)
				size = os.lstat(extracted)[6]
				ResultFile.objects.create(result=self.result, path=member.name, size=size, type='added')
		except tarfile.ReadError:
			pass
		for f in self.report['deleted']:
			rf = ResultFile.objects.create(result=self.result, path=f, type='deleted')
			os.remove(os.path.join(root, f[1:])) #TODO: Fix this to remove starting slash
		os.remove(tarfile_name)
	
	def update(self, request, id):
		self.backup = get_object_or_404(Backup, pk=id)
		self.result = get_object_or_404(Result, backup=self.backup, finished_at=None)
		
		report_file = request.FILES['report']
		self.report = json.loads(report_file.read())
		
		r = PackageReceiver(self.result, callback=self.process_result)
		r.start()
		return {'port': r.port}
	
	create = update
