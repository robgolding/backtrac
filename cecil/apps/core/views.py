from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

@login_required
def index(request):
	return HttpResponseRedirect(reverse('dashboard'))

def dashboard(request, *args, **kwargs):
	kwargs.update({'template': 'dashboard.html'})
	return direct_to_template(request, *args, **kwargs)
