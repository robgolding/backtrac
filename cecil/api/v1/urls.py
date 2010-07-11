from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from handlers import BackupHandler

auth = HttpBasicAuthentication(realm="Backtrac API")
ad = { 'authentication': auth }

backup_handler = Resource(BackupHandler, **ad)

urlpatterns = patterns('',
	
	url(r'^backup/(?P<id>\d+)/', backup_handler),
	
)
