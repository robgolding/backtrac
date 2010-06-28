from django import forms
from django.forms.formsets import formset_factory
from django.forms.formsets import BaseFormSet

from models import Schedule, Rule

class ScheduleForm(forms.ModelForm):
	
	class Meta:
		model = Schedule

class RuleForm(forms.ModelForm):
	
	class Meta:
		model = Rule
		exclude = ['schedule']

RuleFormSet = formset_factory(RuleForm, formset=BaseFormSet, extra=1)
