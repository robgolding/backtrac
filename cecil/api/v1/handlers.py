import os, sys, uuid, json, tarfile, datetime

from django.shortcuts import get_object_or_404
from django.conf import settings
from piston.handler import BaseHandler

from cecil.apps.backups.models import Backup, BackedUpFile
from cecil.apps.clients.models import Client, Checkin

from receiver import PackageReceiver

class CheckinHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request):
		c = Checkin.objects.create(client=request.user)
		return { 'pending': request.user.backup_pending() }
	
	create = update

class BeginBackupHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request):
		backup = Backup.objects.create(client=request.user)
		paths = [ f.path for f in request.user.filepaths.all() ]
		return { 'backup_id': backup.id, 'paths': paths }
	
	create = update

class BackupReceiptHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def process_result(self, tarfile_name):
		root = os.path.join(settings.BACKTRAC_BACKUP_ROOT, '%d' % self.backup.id)
		try:
			t = tarfile.open(tarfile_name, 'r:gz')
			members = t.getmembers()
			for member in members:
				t.extract(member, path=root)
				extracted = os.path.join(root, member.name)
				size = os.lstat(extracted)[6]
				BackedUpFile.objects.create(backup=self.backup, path=member.name, size=size, action='added')
		except tarfile.ReadError:
			pass
		for f in self.report['deleted']:
			rf = BackedUpFile.objects.create(backup=self.backup, path=f, action='deleted')
			os.remove(os.path.join(root, f[1:])) #TODO: Fix this to remove starting slash
		os.remove(tarfile_name)
		
		self.backup.finished_at = datetime.datetime.now()
		self.backup.successful = self.report['result']
		self.backup.save()
	
	def update(self, request):
		self.backup = get_object_or_404(Backup, client=request.user, finished_at=None)
		
		report_file = request.FILES['report']
		self.report = json.loads(report_file.read())
		
		r = PackageReceiver(self.backup, callback=self.process_result)
		r.start()
		return {'port': r.port}
	
	create = update
