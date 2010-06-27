from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from forms import BackupForm

def create_backup(request, template_name='backups/create_backup.html'):
	if request.method == 'POST':
		form = BackupForm(request.POST)
		if form.is_valid():
			backup = form.save()
			return HttpResponseRedirect(reverse('backups_backup_list'))
	else:
		form = BackupForm()
	data = { 'form': form }
	return render_to_response(template_name, data, context_instance=RequestContext(request))
