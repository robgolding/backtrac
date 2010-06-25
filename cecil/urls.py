from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	
	(r'^admin/', include(admin.site.urls)),
)

from django.conf import settings

if settings.SERVE_STATIC:
	urlpatterns += patterns('',
		(r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:],
							'django.views.static.serve',
							{ 'document_root': settings.STATIC_ROOT }
		),
	)
