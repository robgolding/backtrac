import os, sys, uuid, json, tarfile, datetime

from django.shortcuts import get_object_or_404
from django.conf import settings
from piston.handler import BaseHandler

from backtrac.apps.core.utils.storage import Storage
from backtrac.apps.backups.models import Backup, BackedUpFile
from backtrac.apps.clients.models import Client, Checkin

from receiver import PackageReceiver

class CheckinHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request):
		checkin, created = Checkin.objects.get_or_create(client=request.user)
		if not created:
			checkin.save()
		return { 'pending': request.user.backup_pending() }
	
	create = update

class BeginBackupHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def update(self, request):
		backup = Backup.objects.create(client=request.user)
		paths = [ f.path for f in request.user.filepaths.all() ]
		return { 'backup_uuid': backup.uuid, 'paths': paths }
	
	create = update

class BackupReceiptHandler(BaseHandler):
	allowed_methods = ('PUT', 'POST')
	
	def process_result(self, tarfile_name):
		for f in self.report['added']:
			BackedUpFile.objects.create(backup=self.backup, path=f, size=0, action='added') #TODO: add size to report
		for f in self.report['deleted']:
			BackedUpFile.objects.create(backup=self.backup, path=f, action='deleted')
		
		storage = Storage(settings.BACKTRAC_BACKUP_ROOT)
		storage.add_package(self.backup, tarfile_name)
		
		self.backup.finished_at = datetime.datetime.now()
		self.backup.successful = self.report['result']
		self.backup.save()
	
	def process_error(self, exception):
		if not self.backup.finished_at:
			self.backup.finished_at = datetime.datetime.now()
		self.backup.successful = False
		self.backup.save()
		print 'Backup error: %s' % exception
	
	def update(self, request):
		self.backup = get_object_or_404(Backup, client=request.user, finished_at=None)
		
		report_file = request.FILES['report']
		self.report = json.loads(report_file.read())
		
		r = PackageReceiver(self.backup, callback=self.process_result, exception_callback=self.process_error)
		r.start()
		return {'port': r.port}
	
	create = update
