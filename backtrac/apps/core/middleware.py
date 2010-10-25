from django.conf import settings
from django.contrib.auth.views import login
from django.http import HttpResponseRedirect

class RequireLoginMiddleware(object):

    EXCLUDED_URLS = (
        '/accounts/login/',
        '/__debug__/',
        '/api/',
        settings.STATIC_URL,
    )

    def process_request(self, request):
        if request.user.is_anonymous():
            if not request.path.startswith(self.EXCLUDED_URLS):
                if request.POST:
                    return login(request)
                else:
                    return HttpResponseRedirect('%s?next=%s'
                                        % (settings.LOGIN_URL, request.path))
