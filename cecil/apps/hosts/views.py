from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from forms import HostForm

def create_host(request, template_name='hosts/create_host.html'):
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
