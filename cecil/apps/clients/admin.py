from django.contrib import admin

from models import Client, FilePath, Checkin

class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'hostname', 'get_status', 'active',)
    list_display_links = ('id', 'hostname',)
    list_filter = ('active',)

admin.site.register(Client, ClientAdmin)
admin.site.register(FilePath)
admin.site.register(Checkin)
