from django import forms
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.forms.formsets import BaseFormSet, formset_factory
from django.contrib.formtools.wizard import FormWizard

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

class ClientFieldsForm(forms.Form):
    hostname = forms.CharField(max_length=255)
    secret_key = forms.CharField(max_length=255)

class PathForm(forms.Form):
    path = forms.CharField(max_length=255)

PathFormSet = formset_factory(PathForm, formset=BaseFormSet, extra=1)

class ClientWizard(FormWizard):
    """
    The client wizard. Code in `__call__' and `render' written by user `visik7'
    on Django ticket http://code.djangoproject.com/ticket/11112
    """

    __name__ = 'ClientWizard'

    def get_template(self, step):
        if step == 0:
            return 'clients/client_wizard_client.html'
        elif step == 1 or step == 2:
            return 'clients/client_wizard_paths.html'

    def done(self, request, form_list):
        return render_to_response('clients/client_wizard_done.html', {
            'form_data': [form.cleaned_data for form in form_list],
        }, context_instance=RequestContext(request))

    @method_decorator(csrf_protect)
    def __call__(self, request, *args, **kwargs):
        """
        Main method that does all the hard work, conforming to the Django view
        interface.
        """
        if 'extra_context' in kwargs:
            self.extra_context.update(kwargs['extra_context'])
        current_step = self.determine_step(request, *args, **kwargs)
        self.parse_params(request, *args, **kwargs)

        # Sanity check.
        if current_step >= self.num_steps():
            raise Http404('Step %s does not exist' % current_step)

        # Process the current step. If it's valid, go to the next step or call
        # done(), depending on whether any steps remain.
        if request.method == 'POST':
            form = self.get_form(current_step, request.POST)
        else:
            form = self.get_form(current_step)

        if form.is_valid():
            # Validate all the forms. If any of them fail validation, that
            # must mean the validator relied on some other input, such as
            # an external Web site.

            # It is also possible that validation might fail under certain
            # attack situations: an attacker might be able to bypass previous
            # stages, and generate correct security hashes for all the
            # skipped stages by virtue of:
            #  1) having filled out an identical form which doesn't have the
            #     validation (and does something different at the end),
            #  2) or having filled out a previous version of the same form
            #     which had some validation missing,
            #  3) or previously having filled out the form when they had
            #     more privileges than they do now.
            #
            # Since the hashes only take into account values, and not other
            # other validation the form might do, we must re-do validation
            # now for security reasons.
            current_form_list = [self.get_form(i, request.POST) for i in range(current_step)]

            for i, f in enumerate(current_form_list):

                if issubclass(f.__class__, forms.formsets.BaseFormSet):
                    if request.POST.get("hash_%d" % i, '') != self.security_hash(request, f.management_form):
                        return self.render_hash_failure(request, i)
                    for ff in f.forms:
                        if request.POST.get("hash_%d_%s" % (i, ff.prefix)) != self.security_hash(request, ff) :
                            return self.render_hash_failure(request, i)
                else:
                    if request.POST.get("hash_%d" % i, '') != self.security_hash(request, f):
                        return self.render_hash_failure(request, i)

                if not f.is_valid():
                    return self.render_revalidation_failure(request, i, f)
                else:
                    self.process_step(request, f, i)

            # Now progress to processing this step:
            self.process_step(request, form, current_step)
            next_step = current_step + 1


            if next_step == self.num_steps():
                return self.done(request, current_form_list + [form])
            else:
                form = self.get_form(next_step)
                self.step = current_step = next_step

        return self.render(form, request, current_step)

    def render(self, form, request, step, context=None):
            "Renders the given Form object, returning an HttpResponse."
            old_data = request.POST
            prev_fields = []
            if old_data:
                hidden = forms.HiddenInput()
                # Collect all data from previous steps and render it as HTML hidden fields.
                for i in range(step):
                    old_form = self.get_form(i, old_data)
                    hash_name = 'hash_%s' % i
                    #handle formsets
                    if issubclass(old_form.__class__,forms.formsets.BaseFormSet):
                        # do management form and generate hash
                        prev_fields.extend([bf.as_hidden() for bf in old_form.management_form])
                        prev_fields.append(hidden.render(hash_name, old_data.get(hash_name, self.security_hash(request, old_form.management_form))))
                        for f in old_form.forms:
                            # do each form and generate a hash for each
                            hash_name = 'hash_%s_%s' % (i,f.prefix)
                            prev_fields.extend([bf.as_hidden() for bf in f])
                            prev_fields.append(hidden.render(hash_name, old_data.get(hash_name, self.security_hash(request, f))))
                    else:
                        prev_fields.extend([bf.as_hidden() for bf in old_form])
                        prev_fields.append(hidden.render(hash_name, old_data.get(hash_name, self.security_hash(request, old_form))))
            return self.render_template(request, form, ''.join(prev_fields), step, context)

FilePathFormSet = formset_factory(FilePathForm, formset=BaseFormSet, extra=1)
UpdateFilePathFormSet = formset_factory(FilePathForm, formset=BaseFormSet, extra=0)
