from django.conf.urls.defaults import *

from models import Client
import views

urlpatterns = patterns('',
    
    url(r'^$', 'django.views.generic.list_detail.object_list', {
                            'template_name': 'clients/client_list.html',
                            'queryset': Client.objects.select_related()},
                    name='clients_client_list'),
    
    url(r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', {
                            'template_name': 'clients/client_detail.html',
                            'queryset': Client.objects.select_related()},
                            name='clients_client_detail'),
    
    url(r'^(?P<client_id>\d+)/update/$', views.update_client, name='clients_update_client'),
    
    url(r'^(?P<client_id>\d+)/pause/$', views.pause_client, name='clients_pause_client'),
    
    url(r'^(?P<client_id>\d+)/resume/$', views.resume_client, name='clients_resume_client'),
    
    url(r'^(?P<client_id>\d+)/delete/$', views.delete_client, name='clients_delete_client'),
    
    url(r'^create/$', views.create_client, name='clients_create_client'),
    
    # results
    
#   url(r'^(?P<client_id>\d+)/results/(?P<result_id>\d+)$', views.result_detail, {
#                           'template_name': 'clients/client_list.html'}, 
#                   name='clients_result_detail'),
    
)
