from django.contrib import admin

from models import Backup, BackupEvent

class BackupAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'host', 'get_status', 'active',)
	list_filter = ('active',)

admin.site.register(Backup, BackupAdmin)
admin.site.register(BackupEvent)
