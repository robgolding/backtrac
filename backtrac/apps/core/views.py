from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.db.models import Sum

from backtrac.apps.catalog.models import Item, Version

from utils import server_status

@login_required
def index(request):
    return HttpResponseRedirect(reverse('dashboard'))

@login_required
def dashboard(request, *args, **kwargs):
    import os
    from django.conf import settings
    stat = os.statvfs(settings.BACKTRAC_BACKUP_ROOT)
    size = stat.f_blocks * stat.f_frsize
    used = size - stat.f_bavail * stat.f_frsize
    used_pc = int(float(used) / float(size) * 100)
    catalog_size = Version.objects.aggregate(size=Sum('size'))['size']

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
        },
    })

    return direct_to_template(request, *args, **kwargs)

@login_required
def status(request):
    status = server_status()
    r, s = ('running', 200) if status else ('not running', 412)
    return HttpResponse(r, status=s)
