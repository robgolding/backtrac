from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_detail
from django.db import transaction
from django.template.context import RequestContext
from django.contrib import messages

from models import Client
from forms import ClientForm, FilePathFormSet, UpdateFilePathFormSet

@login_required
@transaction.commit_on_success
def create_client(request, template_name='clients/client_form.html'):
    if request.method == 'POST':
        client_form = ClientForm(request.POST)
        filepath_formset = FilePathFormSet(request.POST, prefix='filepaths')
        if all([client_form.is_valid(), filepath_formset.is_valid()]):
            client = client_form.save()
            for form in filepath_formset.forms:
                filepath = form.save(commit=False)
                filepath.client = client
                filepath.save()
            messages.success(request, 'Client created successfully.')
            return HttpResponseRedirect(client.get_absolute_url())
    else:
        client_form = ClientForm()
        filepath_formset = FilePathFormSet(prefix='filepaths')

    data = {
        'client_form': client_form,
        'filepath_formset': filepath_formset,
        'back_link': reverse('clients_client_list'),
    }
    return render_to_response(template_name, data, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def update_client(request, client_id, template_name='clients/client_form.html'):
    client = get_object_or_404(Client, pk=client_id)
    referrer = request.META.get('HTTP_REFERER', '').strip(' ?')
    if request.method == 'POST':
        client_form = ClientForm(request.POST, instance=client)
        filepath_formset = UpdateFilePathFormSet(request.POST, prefix='filepaths')
        if all([client_form.is_valid(), filepath_formset.is_valid()]):
            [j.delete() for j in client.filepaths.all()]
            client = client_form.save()
            client.save()
            for form in filepath_formset.forms:
                filepath = form.save(commit=False)
                filepath.client = client
                filepath.save()
            messages.success(request, 'Client updated successfully.')
            return HttpResponseRedirect(client.get_absolute_url())
    else:
        client_form = ClientForm(instance=client)
        filepaths = client.filepaths.all()
        filepaths_data = [{'path': j.path} for j in filepaths]
        filepath_formset = UpdateFilePathFormSet(initial=filepaths_data, prefix='filepaths')

    if referrer.endswith(client.get_absolute_url()):
        back_link = client.get_absolute_url()
    else:
        back_link = reverse('clients_client_list')

    data = {
        'client': client,
        'client_form': client_form,
        'filepath_formset': filepath_formset,
        'back_link': back_link,
    }
    return render_to_response(template_name, data, context_instance=RequestContext(request))

@login_required
def pause_client(request, client_id, next=None):
    client = get_object_or_404(Client, pk=client_id)
    client.active = False
    client.save()
    if next is None:
        referrer = request.META.get('HTTP_REFERER', '').strip(' ?')
        if referrer.endswith(client.get_absolute_url()):
            next = client.get_absolute_url()
        else:
            next = reverse('clients_client_list')
    messages.success(request, 'Client updated successfully.')
    return HttpResponseRedirect(next)

@login_required
def resume_client(request, client_id, next=None):
    client = get_object_or_404(Client, pk=client_id)
    client.active = True
    client.save()
    if next is None:
        referrer = request.META.get('HTTP_REFERER', '').strip(' ?')
        if referrer.endswith(client.get_absolute_url()):
            next = client.get_absolute_url()
        else:
            next = reverse('clients_client_list')
    messages.success(request, 'Client updated successfully.')
    return HttpResponseRedirect(next)

@login_required
def delete_client(request, client_id, template_name='clients/delete_client.html'):
    client = get_object_or_404(Client, pk=client_id)
    referrer = request.META.get('HTTP_REFERER', '').strip(' ?')
    if request.method == 'POST':
        if request.POST.get('confirm', False):
            client.delete()
            messages.success(request, 'Client deleted successfully.')
            return HttpResponseRedirect(reverse('clients_client_list'))

    if referrer.endswith(client.get_absolute_url()):
        back_link = client.get_absolute_url()
    else:
        back_link = reverse('clients_client_list')

    data = { 'client': client, 'back_link': back_link }
    return render_to_response(template_name, data, context_instance=RequestContext(request))
