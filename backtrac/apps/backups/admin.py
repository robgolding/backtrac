from django.contrib import admin

from models import Backup, BackedUpFile

admin.site.register(Backup)
admin.site.register(BackedUpFile)
