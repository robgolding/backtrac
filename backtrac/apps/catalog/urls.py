from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic.list_detail import object_list, object_detail

from backtrac.apps.clients.models import Client

import views

urlpatterns = patterns('',

    url(r'^$', login_required(object_list), {
                        'template_name': 'catalog/browse.html',
                        'queryset': Client.objects.select_related()},
                    name='catalog_browse'),

   url(r'^(?P<client_id>\d+)/$', views.browse_client, {'path': '/'},
                    name='catalog_browse_client'),

    url(r'^(?P<client_id>\d+)/(?P<path>.*)$', views.browse_route,
                    name='catalog_browse_route'),

)
