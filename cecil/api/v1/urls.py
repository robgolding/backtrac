from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from handlers import *

def host_auth(username, password):
	from cecil.apps.hosts.models import Host
	try:
		return Host.objects.get(hostname=username, secret_key=password)
	except Host.DoesNotExist:
		return None

auth = HttpBasicAuthentication(realm="Backtrac API", auth_func=host_auth)
ad = { 'authentication': auth }

class CsrfExemptResource(Resource):
	def __init__(self, handler, authentication=None):
		super(CsrfExemptResource, self).__init__(handler, authentication)
		self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

checkin_handler = CsrfExemptResource(CheckinHandler, **ad)
backup_handler = CsrfExemptResource(BackupHandler, **ad)
backup_begin_handler = CsrfExemptResource(BackupBeginHandler, **ad)
backup_receipt_handler = CsrfExemptResource(BackupReceiptHandler, **ad)

urlpatterns = patterns('',
	
	url(r'^checkin/$', checkin_handler, name="api_v1_checkin"),
	
	url(r'^backups/(?P<id>\d+)/$', backup_handler, name="api_v1_backup_detail"),
	
	url(r'^backups/(?P<id>\d+)/begin/$', backup_begin_handler, name="api_v1_backup_begin"),
	
	url(r'^backups/(?P<id>\d+)/submit_package/$', backup_receipt_handler, name="api_v1_backup_submit_package"),
	
)
