from django.db import models

class Host(models.Model):
	hostname = models.CharField(max_length=255, unique=True, db_index=True)
	
	@models.permalink
	def get_absolute_url(self):
		return ('hosts_host_detail', [self.id])
	
	def __unicode__(self):
		return self.hostname
