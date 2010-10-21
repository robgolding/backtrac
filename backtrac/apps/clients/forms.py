from django import forms
from django.forms.formsets import BaseFormSet, formset_factory

from models import Client, FilePath

class ClientForm(forms.ModelForm):

    class Meta:
        model = Client

class FilePathForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FilePathForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FilePath
        exclude = ['client']

FilePathFormSet = formset_factory(FilePathForm, formset=BaseFormSet, extra=1)
UpdateFilePathFormSet = formset_factory(FilePathForm, formset=BaseFormSet, extra=0)
