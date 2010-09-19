from django.db import models

class BackupManager(models.Manager):
	def finished(self):
		return self.get_query_set().filter(finished_at__isnull=False)
