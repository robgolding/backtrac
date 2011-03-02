from django.contrib import admin

from models import Item, Version, Event, RestoreJob

admin.site.register(Item)
admin.site.register(Version)
admin.site.register(Event)
admin.site.register(RestoreJob)
