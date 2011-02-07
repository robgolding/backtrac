from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic import DetailView, ListView

from models import Client
import views

urlpatterns = patterns('',

    url(r'^$', login_required(ListView.as_view(
        template_name='clients/client_list.html',
        queryset=Client.objects.select_related(),
    )), name='clients_client_list'),

    url(r'^(?P<pk>\d+)/$', login_required(DetailView.as_view(
        template_name='clients/client_detail.html',
        queryset=Client.objects.select_related(),
    )), name='clients_client_detail'),

    url(r'^(?P<client_id>\d+)/update/$', views.update_client,
        name='clients_update_client'),

    url(r'^(?P<client_id>\d+)/pause/$', views.pause_client,
        name='clients_pause_client'),

    url(r'^(?P<client_id>\d+)/resume/$', views.resume_client,
        name='clients_resume_client'),

    url(r'^(?P<client_id>\d+)/delete/$', views.delete_client,
        name='clients_delete_client'),

    url(r'^create/$', views.CreateClientView.as_view(),
        name='clients_create_client'),

)
