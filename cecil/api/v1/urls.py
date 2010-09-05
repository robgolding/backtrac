from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from handlers import CheckStatusHandler, BackupHandler, BackupReceiptHandler

def host_auth(username, password):
	from cecil.apps.hosts.models import Host
	try:
		return Host.objects.get(hostname=username, secret_key=password)
	except Host.DoesNotExist:
		return None

auth = HttpBasicAuthentication(realm="Backtrac API", auth_func=host_auth)
ad = { 'authentication': auth }

backup_handler = Resource(BackupHandler, **ad)
backup_receipt_handler = Resource(BackupReceiptHandler, **ad)
check_status_handler = Resource(CheckStatusHandler)

urlpatterns = patterns('',
	
	url(r'^check_status/$', check_status_handler, name="api_v1_check_status"),
	
	url(r'^backups/(?P<id>\d+)/$', backup_handler, name="api_v1_backup_detail"),
	
	url(r'^backups/(?P<id>\d+)/submit_package/$', backup_receipt_handler, name="api_v1_backup_submit_package"),
	
)
