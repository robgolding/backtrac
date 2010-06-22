from django.contrib import admin

from models import Backup, BackupEvent, Schedule

class BackupAdmin(admin.ModelAdmin):
	list_display = ('name', 'host', 'next_run', 'interval', 'get_status', 'active',)
	list_filter = ('active',)

admin.site.register(Backup, BackupAdmin)
admin.site.register(BackupEvent)
admin.site.register(Schedule)
