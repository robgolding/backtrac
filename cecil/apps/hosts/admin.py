from django.contrib import admin

from models import Host, Checkin

class HostAdmin(admin.ModelAdmin):
	list_display = ('id', 'hostname',)
	list_display_links = ('id', 'hostname',)

admin.site.register(Host, HostAdmin)
admin.site.register(Checkin)
