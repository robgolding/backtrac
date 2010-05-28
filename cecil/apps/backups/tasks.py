from celery.decorators import task
from celery.task.control import discard_all

from models import Backup

@task()
def execute_backup(backup_id, **kwargs):
	logger = execute_backup.get_logger(**kwargs)
	logger.warning("Executing backup %d" % backup_id)
	
@task()
def resubmit_all_backups(**kwargs):
	logger = resubmit_all_backups.get_logger(**kwargs)
	discard_all()
	for backup in Backup.objects.all():
		r = execute_backup.apply_async(args=[backup.id], eta=backup.next_run)
		backup.task_id = r.task_id
		backup.save()
		logger.warning("Submitted backup '%s' to run at %s" % (backup, backup.next_run))
