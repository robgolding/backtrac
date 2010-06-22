import calendar, datetime

from django.db import models

import fields, tasks

BACKUP_EVENT_TYPE_CHOICES = (
	('started', 'Backup started'),
	('finished', 'Backup finished'),
	('error', 'Backup error'),
)

SCHEDULE_TYPE_CHOICES = (
	('daily', 'Daily'),
	('weekly', 'Weekly'),
	('monthly', 'Monthly'),
)

def ordinal(num):
	if 4 <= num <= 20 or 24 <= num <= 30:
		suffix = 'th'
	else:
		suffix = ['st', 'nd', 'rd'][num % 10 - 1]
	return '%d%s' % (num, suffix)

def construct_datetime(d, **kwargs):
	opts = {
		'year': d.year,
		'month': d.month,
		'day': d.day,
	}
	opts.update(kwargs)
	return datetime.datetime(**opts)

class Schedule(models.Model):
	type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES)
	day = models.PositiveIntegerField(null=True, blank=True)
	time = models.TimeField()
	
	def get_day(self):
		if self.type == 'weekly':
			return calendar.day_name[self.day]
		if self.type == 'monthly':
			return self.day
		return None
	
	def next_occurrence(self):
		now = datetime.datetime.now()
		today = construct_datetime(datetime.datetime.now())
		one_day = datetime.timedelta(days=1)
		one_week = datetime.timedelta(days=7)
		four_weeks = datetime.timedelta(days=28)
		if self.type == 'daily':
			occ = construct_datetime(now,
						hour=self.time.hour, minute=self.time.minute,
						second=self.time.second
					)
			if now > occ:
				return occ + one_day
			else:
				return occ
		if self.type == 'weekly':
			occ = construct_datetime(now,
						day=self.day, hour=self.time.hour,
						minute=self.time.minute, second=self.time.second
					)
			if now > occ:
				return occ + one_week
			else:
				return occ
		if self.type == 'monthly':
			occ = construct_datetime(now, day=self.day, hour=self.time.hour,
						minute=self.time.minute, second=self.time.second)
			if now > occ:
				return construct_datetime(occ + four_weeks, day=self.day)
			else:
				return occ
	
	def __unicode__(self):
		if self.type == 'daily':
			return 'Every day at %s' % self.time
		if self.type == 'weekly':
			return 'Every %s at %s' % (self.get_day(), self.time)
		if self.type == 'monthly':
			return 'Every month on the %s at %s' % (ordinal(self.day), self.time)

class Backup(models.Model):
	name = models.CharField(max_length=200, unique=True)
	host = models.CharField(max_length=200)
	directory = models.CharField(max_length=255)
	next_run = models.DateTimeField()
	interval = fields.TimedeltaField()
	active = models.BooleanField(default=True)
	task_id = models.CharField(max_length=36, null=True, blank=True, editable=False)
	
	def save(self, resubmit=False, *args, **kwargs):
		super(Backup, self).save(*args, **kwargs)
		if resubmit:
			tasks.resubmit_backup(self)
	
	def is_running(self):
		try:
			return self.events.latest().type == 'started'
		except BackupEvent.DoesNotExist:
			return False
	
	def get_status(self):
		if self.is_running():
			return 'running'
		else:
			return 'idle'
	get_status.short_description = 'Status'
	
	def __unicode__(self):
		return self.name

class BackupEvent(models.Model):
	backup = models.ForeignKey(Backup, related_name='events')
	type = models.CharField(max_length=20, choices=BACKUP_EVENT_TYPE_CHOICES)
	occured_at = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s: %s' % (self.get_type_display(), self.backup)
	
	class Meta:
		get_latest_by = 'occured_at'
