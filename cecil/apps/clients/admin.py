from django.contrib import admin

from models import Client

class ClientAdmin(admin.ModelAdmin):
	list_display = ('id', 'hostname',)
	list_display_links = ('id', 'hostname',)

admin.site.register(Client, ClientAdmin)
