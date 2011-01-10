from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

from utils import server_status

@login_required
def index(request):
    return HttpResponseRedirect(reverse('dashboard'))

@login_required
def dashboard(request, *args, **kwargs):
    kwargs.update({'template': 'dashboard.html'})
    return direct_to_template(request, *args, **kwargs)

@login_required
def status(request):
    status = server_status()
    r, s = ('running', 200) if status else ('not running', 412)
    return HttpResponse(r, status=s)
