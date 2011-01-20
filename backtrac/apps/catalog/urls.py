from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic.list_detail import object_list, object_detail

from backtrac.apps.clients.models import Client

import views

urlpatterns = patterns('',

    url(r'^$', views.browse_catalog, name='catalog_browse'),

    url(r'^(?P<client_id>\d+)/$', views.browse_route, {'path': '/'},
                    name='catalog_browse_route'),

    url(r'^(?P<client_id>\d+)/(?P<path>.*)$', views.browse_route,
                    name='catalog_browse_route'),

    url(r'^download/(?P<version_id>[\w-]+)/$', views.download_version, {
                        'view_file': False,},
                    name='catalog_download_version'),

    url(r'^view/(?P<version_id>[\w-]+)/$', views.download_version, {
                        'view_file': True,},
                    name='catalog_view_version'),

)
