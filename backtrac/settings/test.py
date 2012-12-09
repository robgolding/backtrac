ADMINS = () # Django issue #19172

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

BACKTRAC_BACKUP_ROOT = '/tmp/backtrac/test/backups/'
