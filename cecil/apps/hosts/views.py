from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.contrib import messages

from models import Host
from forms import HostForm

def create_host(request, template_name='hosts/host_form.html'):
	if request.method == 'POST':
		form = HostForm(request.POST)
		if form.is_valid():
			host = form.save()
			messages.success(request, 'Host added successfully.')
			return HttpResponseRedirect(host.get_absolute_url())
	else:
		form = HostForm()
	
	data = {
		'form': form,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))

def update_host(request, host_id, template_name='hosts/host_form.html'):
	host = get_object_or_404(Host, pk=host_id)
	referrer = request.META['HTTP_REFERER'].strip(' ?')
	if request.method == 'POST':
		form = HostForm(request.POST, instance=host)
		if form.is_valid():
			host = form.save()
			messages.success(request, 'Host updated successfully.')
			return HttpResponseRedirect(host.get_absolute_url())
	else:
		form = HostForm(instance=host)
	
	if referrer.endswith(host.get_absolute_url()):
		back_link = host.get_absolute_url()
	else:
		back_link = reverse('hosts_host_list')
	
	data = {
		'host': host,
		'form': form,
		'back_link': back_link,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))

def delete_host(request, host_id, template_name='hosts/delete_host.html', next=None):
	host = get_object_or_404(Host, pk=host_id)
	referrer = request.META['HTTP_REFERER'].strip(' ?')
	if request.method == 'POST':
		if request.POST.get('confirm', False):
			host.delete()
			messages.success(request, "Host deleted successfully.")
			return HttpResponseRedirect(reverse('hosts_host_list'))
	
	if referrer.endswith(host.get_absolute_url()):
		back_link = host.get_absolute_url()
	else:
		back_link = reverse('hosts_host_list')
	
	data = { 'host': host, 'back_link': back_link }
	return render_to_response(template_name, data, context_instance=RequestContext(request))
