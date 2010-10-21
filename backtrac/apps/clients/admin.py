from django.contrib import admin

from models import Client, FilePath

class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'hostname', 'active',)
    list_display_links = ('id', 'hostname',)
    list_filter = ('active',)

admin.site.register(Client, ClientAdmin)
admin.site.register(FilePath)
