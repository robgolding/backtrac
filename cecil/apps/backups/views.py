from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.contrib import messages

from models import Backup
from forms import BackupForm, JobFormSet, UpdateJobFormSet
from cecil.apps.schedules.forms import ScheduleForm, RuleFormSet, UpdateRuleFormSet

def create_backup(request, template_name='backups/backup_form.html'):
	if request.method == 'POST':
		backup_form = BackupForm(request.POST)
		schedule_form = ScheduleForm(request.POST)
		rule_formset = RuleFormSet(request.POST, prefix='rules')
		job_formset = JobFormSet(request.POST, prefix='jobs')
		if all([backup_form.is_valid(), schedule_form.is_valid(),
				rule_formset.is_valid(), job_formset.is_valid()]):
			schedule = schedule_form.save()
			for form in rule_formset.forms:
				rule = form.save(commit=False)
				rule.schedule = schedule
				rule.save()
			backup = backup_form.save(commit=False)
			backup.schedule = schedule
			backup.save()
			for form in job_formset.forms:
				job = form.save(commit=False)
				job.backup = backup
				job.save()
			messages.success(request, 'Backup created successfully.')
			return HttpResponseRedirect(backup.get_absolute_url())
	else:
		backup_form = BackupForm()
		schedule_form = ScheduleForm()
		rule_formset = RuleFormSet(prefix='rules')
		job_formset = JobFormSet(prefix='jobs')
	
	data = {
		'backup_form': backup_form,
		'schedule_form': schedule_form,
		'rule_formset': rule_formset,
		'job_formset': job_formset,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))

def update_backup(request, backup_id, template_name='backups/backup_form.html'):
	backup = get_object_or_404(Backup, pk=backup_id)
	schedule = backup.schedule
	if request.method == 'POST':
		backup_form = BackupForm(request.POST, instance=backup)
		schedule_form = ScheduleForm(request.POST, instance=schedule)
		rule_formset = UpdateRuleFormSet(request.POST, prefix='rules')
		job_formset = UpdateJobFormSet(request.POST, prefix='jobs')
		if all([backup_form.is_valid(), schedule_form.is_valid(),
				rule_formset.is_valid(), job_formset.is_valid()]):
			[r.delete() for r in schedule.rules.all()]
			[j.delete() for j in backup.jobs.all()]
			schedule = schedule_form.save()
			for form in rule_formset.forms:
				rule = form.save(commit=False)
				rule.schedule = schedule
				rule.save()
			backup = backup_form.save(commit=False)
			backup.schedule = schedule
			backup.save()
			for form in job_formset.forms:
				job = form.save(commit=False)
				job.backup = backup
				job.save()
			messages.success(request, 'Backup updated successfully.')
			return HttpResponseRedirect(backup.get_absolute_url())
	else:
		backup_form = BackupForm(instance=backup)
		schedule_form = ScheduleForm(instance=schedule)
		rules = backup.schedule.rules.all()
		jobs = backup.jobs.all()
		rules_data = [{'frequency': r.frequency, 'interval': r.interval} for r in rules]
		jobs_data = [{'path': j.path} for j in jobs]
		rule_formset = UpdateRuleFormSet(initial=rules_data, prefix='rules')
		job_formset = UpdateJobFormSet(initial=jobs_data, prefix='jobs')
	
	data = {
		'backup': backup,
		'backup_form': backup_form,
		'schedule_form': schedule_form,
		'rule_formset': rule_formset,
		'job_formset': job_formset,
	}
	return render_to_response(template_name, data, context_instance=RequestContext(request))

def pause_backup(request, backup_id, next=None):
	backup = get_object_or_404(Backup, pk=backup_id)
	backup.active = False
	backup.save()
	if next is None:
		next = reverse('backups_backup_list')
	return HttpResponseRedirect(next)

def resume_backup(request, backup_id, next=None):
	backup = get_object_or_404(Backup, pk=backup_id)
	backup.active = True
	backup.save()
	if next is None:
		next = reverse('backups_backup_list')
	return HttpResponseRedirect(next)

def delete_backup(request, backup_id, template_name='backups/delete_backup.html', next=None):
	backup = get_object_or_404(Backup, pk=backup_id)
	if request.method == 'POST':
		if request.POST.get('confirm', False):
			backup.delete()
			messages.success(request, "Backup deleted successfully.")
			return HttpResponseRedirect(reverse('backups_backup_list'))
	data = { 'backup': backup }
	return render_to_response(template_name, data, context_instance=RequestContext(request))
