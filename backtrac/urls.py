from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from backtrac.apps.core import views

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    url(r'^$', views.index, name='index'),

    url(r'^dashboard/$', views.dashboard, name='dashboard'),

    url(r'^accounts/login/', 'django.contrib.auth.views.login',
                name='auth_login'),

    url(r'^accounts/logout/', 'django.contrib.auth.views.logout_then_login',
                name='auth_logout'),

    (r'^clients/', include('backtrac.apps.clients.urls')),

    (r'^browse/', include('backtrac.apps.catalog.urls')),

)

from django.conf import settings

if settings.SERVE_STATIC:
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:],
                            'django.views.static.serve',
                            { 'document_root': settings.STATIC_ROOT }
        ),
    )
