from django.conf.urls.defaults import *

from backtrac.apps.core import views

config_patterns = patterns('',

    url(r'^$', views.config, name='core_config'),

)
