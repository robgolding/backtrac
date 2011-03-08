from django import forms
from django.forms.formsets import BaseFormSet, formset_factory

class ExclusionForm(forms.Form):
    glob = forms.CharField(max_length=255)

ExclusionFormSet = formset_factory(ExclusionForm, formset=BaseFormSet, extra=1)
