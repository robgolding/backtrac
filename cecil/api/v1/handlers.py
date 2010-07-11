from piston.handler import BaseHandler

from cecil.apps.backups.models import Backup

class BackupHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Backup
	
#	def read(self, request, post_slug):
