from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from forms import BackupForm
from cecil.apps.schedules.forms import ScheduleForm, RuleFormSet

def create_backup(request, template_name='backups/create_backup.html'):
	if request.method == 'POST':
		backup_form = BackupForm(request.POST)
		schedule_form = ScheduleForm(request.POST)
		rule_formset = RuleFormSet(request.POST)
		if backup_form.is_valid() and schedule_form.is_valid() and rule_formset.is_valid():
			schedule = schedule_form.save()
			for form in rule_formset.forms:
				rule = form.save(commit=False)
				rule.schedule = schedule
				rule.save()
			backup = backup_form.save(commit=False)
			backup.schedule = schedule
			backup.save()
			return HttpResponseRedirect(backup.get_absolute_url())
	else:
		backup_form = BackupForm()
		schedule_form = ScheduleForm()
		rule_formset = RuleFormSet()
	
	data = {
		'backup_form': backup_form,
		'schedule_form': schedule_form,
		'rule_formset': rule_formset,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))
