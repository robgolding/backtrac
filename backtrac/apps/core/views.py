from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

from utils import check_daemon_status

@login_required
def index(request):
    return HttpResponseRedirect(reverse('dashboard'))

@login_required
def dashboard(request, *args, **kwargs):
    kwargs.update({'template': 'dashboard.html'})
    return direct_to_template(request, *args, **kwargs)

@login_required
def status(request):
    from multiprocessing import Process, Queue

    q = Queue()
    p = Process(target=check_daemon_status, args=[q,])
    p.start()
    p.join()
    r, s = ('running', 200) if q.get() else ('not running', 412)
    return HttpResponse(r, status=s)
