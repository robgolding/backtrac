import datetime

from django.db.models import get_model

from celery.decorators import task
from celery.task.control import revoke, discard_all

def resubmit_backup(backup, clear_old_task=True):
	if clear_old_task and backup.task_id is not None:
		revoke(backup.task_id)
	
	while backup.next_run <= datetime.datetime.now():
		backup.next_run += datetime.timedelta(seconds=backup.interval)
	
	r = execute_backup.apply_async(args=[backup.id], eta=backup.next_run)
	backup.task_id = r.task_id
	backup.save(resubmit=False)
	
	return (backup.task_id, backup.next_run)

@task()
def execute_backup(backup_id, **kwargs):
	Backup = get_model('backups', 'Backup')
	BackupEvent = get_model('backups', 'BackupEvent')
	
	logger = execute_backup.get_logger(**kwargs)
	backup = Backup.objects.get(id=backup_id)
	
	_, next_run = resubmit_backup(backup)
	logger.warning("Submitted backup '%s' to run at %s" % (backup, next_run))
	
	BackupEvent.objects.create(type='started', backup=backup)
	logger.warning("Added 'started' event to database")
	
	logger.warning("Executing backup %d" % backup.id)
	
@task()
def resubmit_all_backups(**kwargs):
	Backup = get_model('backups', 'Backup')
	
	logger = resubmit_all_backups.get_logger(**kwargs)
	discard_all()
	for backup in Backup.objects.all():
		_, next_run = resubmit_backup(backup, clear_old_task=False)
		logger.warning("Submitted backup '%s' to run at %s" % (backup, next_run))
