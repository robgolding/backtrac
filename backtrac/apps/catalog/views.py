import os, mimetypes
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_detail
from django.db import transaction
from django.template.context import RequestContext
from django.contrib import messages

from backtrac.server.utils import get_storage_for
from backtrac.apps.clients.models import Client

from models import Item, Version
from utils import normpath

@login_required
def browse_route(request, client_id, path='/'):
    client = get_object_or_404(Client, pk=client_id)
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
    }

    return render_to_response(template_name, data,
                              context_instance=RequestContext(request))

@login_required
def browse_directory(request, client, item,
                  template_name='catalog/browse_client.html'):
    if item is None:
        items = client.items.filter(parent=None).select_related('client',
                                                            'latest_version')
    else:
        items = item.children.select_related('client', 'latest_version')

    data = {
        'client': client,
        'item': item,
        'items': items,
    }

    return render_to_response(template_name, data,
                              context_instance=RequestContext(request))

@login_required
def download_version(request, version_id, view_file=True):
    version = get_object_or_404(Version, pk=version_id)
    item = version.item
    storage = get_storage_for(item.client)

    f = storage.get(item.path, version.pk)
    contents = f.read()
    mimetype, encoding = mimetypes.guess_type(item.name)
    mimetype = mimetype or 'application/octet-stream'
    content_disposition = 'filename=%s' % item.name
    if not view_file:
        content_disposition = 'attachment; ' + content_disposition

    response = HttpResponse(FileWrapper(f), content_type=mimetype)
    response = HttpResponse(contents, mimetype=mimetype)
    response['Content-Length'] = len(contents)
    response['Content-Disposition'] = content_disposition
    if encoding:
        response['Content-Encoding'] = encoding
    return response
