from django.conf.urls.defaults import *

urlpatterns = patterns('',
	
	(r'^v1/', include('backtrac.api.v1.urls')),
	
)
