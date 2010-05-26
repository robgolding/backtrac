from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

EVENT_TYPE_CHOICES = (
	('backup_started', 'Backup started'),
	('backup_finished', 'Backup finished'),
	('backup_error', 'Backup error'),
)

class Event(models.Model):
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey('content_type', 'object_id')
	type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
	details = models.TextField(null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s: %s' % (self.get_type_display(), self.content_object)
