from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.db.models import Sum
from django.conf import settings

from backtrac.apps.catalog.models import Item, Version, Event

from backtrac.server.storage import Storage
from backtrac.client import client

@login_required
def index(request):
    return HttpResponseRedirect(reverse('dashboard'))

@login_required
def dashboard(request, *args, **kwargs):
    storage = Storage(settings.BACKTRAC_BACKUP_ROOT)
    size = storage.get_total_bytes()
    used = storage.get_used_bytes()
    used_pc = int(float(used) / float(size) * 100)
    catalog_size = Version.objects.aggregate(size=Sum('size'))['size']

    events = Event.objects.select_related()[:10]

    stats = {
        'size': size,
        'used': used,
        'used_pc': used_pc,
        'catalog_size': catalog_size,
    }

    kwargs.update({
        'template': 'dashboard.html',
        'extra_context': {
            'stats': stats,
            'events': events,
        },
    })

    return direct_to_template(request, *args, **kwargs)

@login_required
def status(request):
    running = client.get_server_status()
    r, s = ('running', 200) if running else ('not running', 412)
    return HttpResponse(r, status=s)
