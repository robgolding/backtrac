import re
import fnmatch

from django.db import models

class GlobalExclusion(models.Model):
    glob = models.CharField(max_length=255)

    def get_regex(self):
        regex = fnmatch.translate(self.glob)
        return re.compile(regex)

    def __unicode__(self):
        return 'Exclude %s' % self.glob
