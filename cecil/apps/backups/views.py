from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from models import Backup
from forms import BackupForm
from cecil.apps.schedules.forms import ScheduleForm, RuleFormSet, UpdateRuleFormSet

def create_backup(request, template_name='backups/backup_form.html'):
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

def update_backup(request, backup_id, template_name='backups/backup_form.html'):
	backup = get_object_or_404(Backup, pk=backup_id)
	schedule = backup.schedule
	if request.method == 'POST':
		backup_form = BackupForm(request.POST, instance=backup)
		schedule_form = ScheduleForm(request.POST, instance=schedule)
		rule_formset = UpdateRuleFormSet(request.POST)
		if backup_form.is_valid() and schedule_form.is_valid() and rule_formset.is_valid():
			[r.delete() for r in schedule.rules.all()]
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
		backup_form = BackupForm(instance=backup)
		schedule_form = ScheduleForm(instance=schedule)
		rules = backup.schedule.rules.all()
		rules_data = [{'frequency': r.frequency, 'interval': r.interval} for r in rules]
		rule_formset = UpdateRuleFormSet(initial=rules_data)
	
	data = {
		'backup': backup,
		'backup_form': backup_form,
		'schedule_form': schedule_form,
		'rule_formset': rule_formset,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))
