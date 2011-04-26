import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.template.context import RequestContext
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.conf import settings

from backtrac.client import client
from backtrac.server.storage import Storage
from backtrac.apps.core.models import GlobalExclusion
from backtrac.apps.core.forms import ExclusionFormSet
from backtrac.apps.catalog.models import Version, Event

CATALOG_SIZE_HISTORY_CACHE_KEY = 'catalog_size_history'

def generate_catalog_graph_data():
    version_qs = Version.objects.all()
    max_date = datetime.datetime.now()
    size_history = []
    while len(version_qs) > 0:
        s = version_qs.aggregate(size=Sum('size'))['size']
        size_history.append([max_date, s])
        max_date -= datetime.timedelta(days=1)
        version_qs = version_qs.filter(backed_up_at__lt=max_date)
    return size_history

def get_catalog_graph_data():
    data = cache.get(CATALOG_SIZE_HISTORY_CACHE_KEY, None)
    if data is None:
        data = generate_catalog_graph_data()
        now = datetime.datetime.now()
        today = datetime.datetime(year=now.year, month=now.month, day=now.day)
        tomorrow = today + datetime.timedelta(days=1)
        timeout = (tomorrow - today()).seconds
        cache.set(CATALOG_SIZE_HISTORY_CACHE_KEY, data, timeout)
    return data

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
    size_history = get_catalog_graph_data()

    events = Event.objects.select_related()[:10]

    stats = {
        'size': size,
        'used': used,
        'used_pc': used_pc,
        'catalog_size': catalog_size,
        'size_history': size_history,
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
@transaction.commit_on_success
def config(request, template_name='config.html'):
    if request.method == 'POST':
        exclusion_formset = ExclusionFormSet(request.POST, prefix='exclusions')
        if exclusion_formset.is_valid():
            [e.delete() for e in GlobalExclusion.objects.all()]
            for form in exclusion_formset:
                glob = form.cleaned_data.get('glob', None)
                if glob:
                    GlobalExclusion.objects.create(glob=glob)
            messages.success(request, 'Configuration updated successfully')
            return HttpResponseRedirect(reverse('core_config'))
    else:
        exclusions = GlobalExclusion.objects.all()
        exclusions_data = [{'glob': e.glob} for e in exclusions]
        exclusion_formset = ExclusionFormSet(initial=exclusions_data,
                                             prefix='exclusions')

    data = {
        'exclusion_formset': exclusion_formset,
    }
    return render_to_response(template_name, data,
                              context_instance=RequestContext(request))

@login_required
def status(request):
    running = client.get_server_status()
    r, s = ('running', 200) if running else ('not running', 412)
    return HttpResponse(r, status=s)
