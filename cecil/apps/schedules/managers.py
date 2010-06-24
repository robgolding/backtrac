from django.db import models
from django.contrib.contenttypes.models import ContentType

class ScheduleManager(models.Manager):
	def get_for_object(self, obj):
		"""
		Create a queryset matching all schedules associated with
		the given object.
		"""
		ctype = ContentType.objects.get_for_model(obj)
		return self.filter(content_type__pk=ctype.pk, object_id=obj.pk)
