import os

from default import *

SERVE_MEDIA = True
PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DATABASES = {
	'default': {
		'ENGINE': 'sqlite3',
		'NAME': os.path.join(PATH, 'dev.db'),
	}
}

# For debug toolbar.
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = ('127.0.0.1',)
INSTALLED_APPS += ('debug_toolbar',)
DEBUG_TOOLBAR_CONFIG = {
	'INTERCEPT_REDIRECTS': False,
}
