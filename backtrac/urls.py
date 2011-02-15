from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

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

handler500 = lambda x: direct_to_template(x, '500.html')

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^500/$', handler500),
        (r'^404/$', 'django.views.generic.simple.direct_to_template', {
            'template': '404.html'
        }),
    )
