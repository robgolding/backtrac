from django.conf import settings
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect

class RequireLoginMiddleware(object):
    def __init__(self):
	    self.login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
	    self.static_url = getattr(settings, 'STATIC_URL', '/static/')
	
    def process_request(self, request):
        if request.user.is_anonymous():
        	if request.path != self.login_url and not request.path.startswith(self.static_url):
		        if request.POST:
		            return login(request)
		        else:
		            return HttpResponseRedirect('%s?next=%s' % (self.login_url, request.path))
