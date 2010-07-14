from django.contrib import admin

from models import Backup, Job, Run

class BackupAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'client', 'get_status', 'active',)
	list_display_links = ('id', 'name',)
	list_filter = ('active',)

admin.site.register(Backup, BackupAdmin)
admin.site.register(Job)
admin.site.register(Run)
