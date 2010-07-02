from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from models import Host
from forms import HostForm

def create_host(request, template_name='hosts/host_form.html'):
	if request.method == 'POST':
		form = HostForm(request.POST)
		if form.is_valid():
			host = form.save()
			return HttpResponseRedirect(host.get_absolute_url())
	else:
		form = HostForm()
	
	data = {
		'form': form,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))

def update_host(request, host_id, template_name='hosts/host_form.html'):
	host = get_object_or_404(Host, pk=host_id)
	if request.method == 'POST':
		form = HostForm(request.POST, instance=host)
		if form.is_valid():
			host = form.save()
			return HttpResponseRedirect(host.get_absolute_url())
	else:
		form = HostForm(instance=host)
	
	data = {
		'host': host,
		'form': form,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))
