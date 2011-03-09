import os, mimetypes
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list, object_detail
from django.db import transaction
from django.template.context import RequestContext
from django.contrib import messages
from django.conf import settings

from backtrac.server.storage import Storage
from backtrac.apps.clients.models import Client
from backtrac.apps.catalog.models import Item, Version, Event, RestoreJob
from backtrac.apps.catalog.utils import normpath
from backtrac.utils import get_mimetype

@login_required
def browse_catalog(request, template_name='catalog/browse.html'):
    kwargs = {
        'queryset': Client.objects.select_related(),
        'template_name': template_name,
        'extra_context': {
            'events': Event.objects.select_related()[:10],
        }
     }
    return object_list(request, **kwargs)

@login_required
def browse_route(request, client_id, path='/'):
    client = get_object_or_404(Client, id=client_id)
    path = normpath(path)

    if path == '/':
        item = None
    else:
        item = get_object_or_404(Item, client=client, path=path)

    if item is None or item.type == 'd':
        return browse_directory(request, client, item)
    elif item.type == 'f':
        return view_file(request, client, item)

@login_required
def view_file(request, client, item,
                  template_name='catalog/view_file.html'):

    data = {
        'client': client,
        'item': item,
        'versions': item.versions.all(),
    }

    return render_to_response(template_name, data,
                              context_instance=RequestContext(request))

@login_required
def browse_directory(request, client, item,
                  template_name='catalog/browse_client.html'):
    show_deleted = request.GET.get('deleted', False) == '1'

    if item is not None and item.deleted:
        if not show_deleted and not hasattr(request.GET, 'deleted'):
            show_deleted = True

    items = Item.objects.all()
    if show_deleted:
        items = Item.objects.all()
    else:
        items = Item.objects.present()

    if item is None:
        items = items.filter(client=client, parent=None)
    else:
        items = items.filter(parent=item)

    items = items.select_related('client', 'latest_version')
    events = Event.objects.filter(item__client=client).select_related()[:10]

    data = {
        'client': client,
        'item': item,
        'items': items,
        'events': events,
        'show_deleted': show_deleted,
    }

    return render_to_response(template_name, data,
                              context_instance=RequestContext(request))

@login_required
def download_version(request, version_id, view_file=True):
    version = get_object_or_404(Version, id=version_id).resolve_original()
    item = version.item
    storage = Storage(settings.BACKTRAC_BACKUP_ROOT)

    f = storage.get(item.client.hostname, item.path, version.id)

    mimetype = get_mimetype(f)
    contents = f.read()

    #TODO: Fix this so we don't have to load the file into memory first
    #response = HttpResponse(FileWrapper(f))
    response = HttpResponse(contents)

    if view_file and mimetype.startswith('text/'):
        response['Content-Disposition'] = 'inline'
        response['Content-Transfer-Encoding'] = 'binary'
        response['Content-Type'] = 'text/plain'
    else:
        response['Content-Disposition'] = 'attachment; filename=%s' % item.name
        response['Content-Length'] = len(contents)
        response['Content-Type'] = 'application/octet-stream'

    return response

@login_required
def restore_version(request, version_id):
    version = get_object_or_404(Version, id=version_id)
    RestoreJob.objects.create(client=version.item.client, version=version)
    messages.success(request, 'File \'%s\' queued for restoration to %s' % \
                     (version.item.name, version.item.client.hostname))
    return HttpResponseRedirect(version.item.get_absolute_url())
