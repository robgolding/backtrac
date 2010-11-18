from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_detail
from django.db import transaction
from django.template.context import RequestContext
from django.contrib import messages

from backtrac.apps.clients.models import Client
from models import Item, Version

@login_required
def browse(request, template_name='catalog/browse.html'):
    pass

@login_required
def browse_client(request, client_id, path='/',
                  template_name='catalog/browse_client.html'):
    client = get_object_or_404(Client, pk=client_id)

    path = filter(lambda x:x, path.split('/'))
    item = None
    for name in path:
        item = get_object_or_404(Item, client=client, parent=item, name=name)

    items = Item.objects.filter(client=client, parent=item)
    print items

    data = {
        'items': items,
    }

    return render_to_response(template_name, data,
                              context_instance=RequestContext(request))
