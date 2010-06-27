from django.conf.urls.defaults import *

from models import Backup
import views

urlpatterns = patterns('',
	
	url(r'^$', 'django.views.generic.list_detail.object_list', {
							'template_name': 'backups/backup_list.html',
							'queryset': Backup.objects.all()},
					name='backups_backup_list'),
	
	url(r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', {
							'template_name': 'backups/backup_detail.html',
							'queryset': Backup.objects.all()},
							name='backups_backup_detail'),
	
	url(r'^create/$', views.create_backup, name='backups_create_backup'),
	
)
