from django.db import models

class Host(models.Model):
	hostname = models.CharField(max_length=255, unique=True, db_index=True)
	
	def __unicode__(self):
		return self.hostname