from django.http import HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.formtools.wizard import FormWizard
from django.contrib import messages

from backtrac.apps.clients.models import Client
from backtrac.apps.catalog.models import Version, RestoreJob

class RestoreForm1(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.all(),
                                    required=False)

class RestoreForm2(forms.Form):
    path = forms.CharField(max_length=255, required=False)

class RestoreWizard(FormWizard):
    __name__ = 'RestoreWizard'

    def parse_params(self, request, version_id):
        self.version = get_object_or_404(Version, id=version_id)
        self.initial = {
            0: { 'client': self.version.item.client },
            1: { 'path': self.version.item.path },
        }

    def get_template(self, step):
        return 'catalog/restore_wizard.html'

    def process_step(self, request, form, step):
        self.extra_context.update({
            'item': self.version.item,
            'version': self.version,
        })

    def done(self, request, form_list):
        client = form_list[0].cleaned_data['client']
        path = form_list[1].cleaned_data['path']

        RestoreJob.objects.create(version=self.version,
                                  destination_client=client,
                                  destination_path=path)
        messages.success(request, 'File \'%s\' queued for restoration to %s' % \
                         (self.version.item.name, client.hostname))
        return HttpResponseRedirect(self.version.item.get_absolute_url())
