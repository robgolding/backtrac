from django.contrib import admin

from models import Directory, File, FileVersion

admin.site.register(Directory)
admin.site.register(File)
admin.site.register(FileVersion)
