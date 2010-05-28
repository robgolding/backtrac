from tasks import resubmit_all_backups

def resubmit_all():
	return resubmit_all_backups.delay()
