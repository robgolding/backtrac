import uuid

from django.db import models

import managers

BACKEDUPFILE_ACTION_CHOICES = (
    ('deleted', 'Deleted'),
    ('added', 'Added'),
    ('error', 'Error'),
)

class Backup(models.Model):
    uuid = models.CharField(max_length=36, db_index=True, blank=True)
    client = models.ForeignKey('clients.Client', related_name='backups')
    successful = models.BooleanField()
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    size = models.BigIntegerField(default=0, blank=True)
    
    objects = managers.BackupManager()
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.uuid = uuid.uuid4()
        super(Backup, self).save(*args, **kwargs)
    
    @models.permalink
    def get_absolute_url(self):
        return ('backups_backup_detail', [self.id])
    
    def is_finished(self):
        return self.finished_at is not None
    
    def get_status(self):
        if not self.finished_at:
            return 'running'
        if self.successful:
            return 'success'
        else:
            return 'error'
    
    def __unicode__(self):
        return '%s (%s)' % (self.client.hostname, self.started_at)
    
    class Meta:
        ordering = ('-started_at',)
        get_latest_by = 'started_at'

class BackedUpFile(models.Model):
    backup = models.ForeignKey(Backup, related_name='files')
    path = models.CharField(max_length=255, db_index=True)
    size = models.BigIntegerField(null=True, blank=True)
    action = models.CharField(max_length=20, db_index=True, choices=BACKEDUPFILE_ACTION_CHOICES)
    
    def __unicode__(self):
        return '%s \'%s\'' % (self.get_action_display(), self.path)
