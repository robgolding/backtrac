from django.contrib import admin

from models import Backup, BackupEvent

admin.site.register(Backup)
admin.site.register(BackupEvent)
