import time, datetime, random

from django.db.models import get_model

from celery.decorators import task
from celery.task.control import revoke, discard_all

def resubmit_backup(backup, clear_old_task=True):
	if clear_old_task and backup.task_id is not None:
		revoke(backup.task_id)
	
	next = backup.schedule.get_next_occurrence()
	
	if not next:
		return
	
	r = execute_backup.apply_async(args=[backup.id], eta=next)
	
	backup.task_id = r.task_id
	backup.save()
	
	return (backup.task_id, next)

@task()
def execute_backup(backup_id, **kwargs):
	Backup = get_model('backups', 'Backup')
	
	logger = execute_backup.get_logger(**kwargs)
	backup = Backup.objects.get(id=backup_id)
	
	_, next_run = resubmit_backup(backup)
	print "Submitted backup '%s' to run at %s" % (backup, next_run)
	
	print "Executed backup '%s' [%d]" % (backup, backup.id)
	
@task()
def resubmit_all_backups(**kwargs):
	Backup = get_model('backups', 'Backup')
	
	logger = resubmit_all_backups.get_logger(**kwargs)
	discard_all()
	for backup in Backup.objects.all():
		resubmit_backup(backup, clear_old_task=False)
