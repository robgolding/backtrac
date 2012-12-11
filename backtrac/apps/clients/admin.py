from django.contrib import admin

from models import Client, Status, FilePath

class ClientAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'active',)
    list_filter = ('active',)

admin.site.register(Client, ClientAdmin)
admin.site.register(Status)
admin.site.register(FilePath)
