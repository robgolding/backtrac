from django.conf import settings
from django.conf.urls.defaults import *

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
admin.autodiscover()

from backtrac.apps.core import views

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    url(r'^$', views.index, name='index'),

    url(r'^dashboard/$', views.dashboard, name='dashboard'),

    url(r'^status/', views.status, name='status'),

    url(r'^accounts/login/', 'django.contrib.auth.views.login',
                name='auth_login'),

    url(r'^accounts/logout/', 'django.contrib.auth.views.logout_then_login',
                name='auth_logout'),

    (r'^clients/', include('backtrac.apps.clients.urls')),

    (r'^catalog/', include('backtrac.apps.catalog.urls')),

)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
