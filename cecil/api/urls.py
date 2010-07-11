from django.conf.urls.defaults import *

urlpatterns = patterns('',
	
	(r'^v1/', include('cecil.api.v1.urls')),
	
)
