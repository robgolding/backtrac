from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from handlers import BackupHandler

def host_auth(username, password):
	from cecil.apps.hosts.models import Host
	try:
		return Host.objects.get(hostname=username, secret_key=password)
	except Host.DoesNotExist:
		return None

auth = HttpBasicAuthentication(realm="Backtrac API", auth_func=host_auth)
ad = { 'authentication': auth }

backup_handler = Resource(BackupHandler, **ad)

urlpatterns = patterns('',
	
	url(r'^backup/(?P<id>\d+)/', backup_handler),
	
)
