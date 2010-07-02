from django.conf.urls.defaults import *

from models import Host
import views

urlpatterns = patterns('',
	
	url(r'^$', 'django.views.generic.list_detail.object_list', {
							'template_name': 'hosts/host_list.html',
							'queryset': Host.objects.all()},
					name='hosts_host_list'),
	
	url(r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', {
							'template_name': 'hosts/host_detail.html',
							'queryset': Host.objects.all()},
							name='hosts_host_detail'),
	
	url(r'^(?P<host_id>\d+)/update/$', views.update_host, name='hosts_update_host'),
	
	url(r'^create/$', views.create_host, name='hosts_create_host'),
	
)
