from django.db import models

class BackupManager(models.Manager):
	def active(self):
		return self.get_query_set().filter(active=True)
