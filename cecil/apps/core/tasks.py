from celery.decorators import task
	
@task()
def check_status(**kwargs):
	return True
