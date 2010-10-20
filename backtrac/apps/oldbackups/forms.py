from django import forms
from django.forms.formsets import BaseFormSet, formset_factory

from models import Backup, Job

class BackupForm(forms.ModelForm):
	
	class Meta:
		model = Backup
		exclude = ['schedule']

class JobForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(JobForm, self).__init__(*args, **kwargs)
	
	class Meta:
		model = Job
		exclude = ['backup']

JobFormSet = formset_factory(JobForm, formset=BaseFormSet, extra=1)
UpdateJobFormSet = formset_factory(JobForm, formset=BaseFormSet, extra=0)
