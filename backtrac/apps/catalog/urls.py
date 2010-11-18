from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic.list_detail import object_list, object_detail

import views

urlpatterns = patterns('',

#   url(r'^$', login_required(object_list), {
#                   'template_name': 'clients/client_list.html',
#                       'queryset': Client.objects.select_related()},
#                   name='clients_client_list'),

    url(r'^$', views.browse, name='catalog_browse'),

    url(r'^(?P<client_id>\d+)/(?P<path>.*)$', views.browse_client,
                    name='catalog_browse_client'),

)
