import datetime
from dateutil import rrule

from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _

import managers

FREQUENCY_CHOICES = (
	('YEARLY', _('Yearly')),
	('MONTHLY', _('Monthly')),
	('WEEKLY', _('Weekly')),
	('DAILY', _('Daily')),
	('HOURLY', _('Hourly')),
	('MINUTELY', _('Minutely')),
	('SECONDLY', _('Secondly'))
)

class Schedule(models.Model):
	"""
	Model to represent a schedule, which consists of a start date and multiple
	'rules' - each of which determines how often the given event recurs.
	"""
	start_date = models.DateTimeField(_('start date'))
	
	objects = managers.ScheduleManager()
	
	def get_next_occurrence(self):
		occs = sorted([r.get_next_occurrence() for r in self.rules.all()])
		return occs[0] if occs else None
	
	def __unicode__(self):
		return '[Schedule] %d' % self.id

class Rule(models.Model):
	"""
	Simple model to represent a python-dateutil rrule object.
	
	Limited functionality only allows the frequency and interval
	to be recorded, which is all that is needed for this application.
	"""
	frequency = models.CharField(_('frequency'), choices=FREQUENCY_CHOICES,
									max_length=10)
	interval = models.PositiveIntegerField(_('interval'), default=1)
	
	schedule = models.ForeignKey(Schedule, related_name='rules')
	
	def get_rrule_object(self):
		frequency = eval('rrule.%s' % self.frequency)
		return rrule.rrule(frequency, interval=self.interval,
						dtstart=self.schedule.start_date)
	
	def get_next_occurrence(self):
		return self.get_rrule_object().after(datetime.datetime.now())
	
	def __unicode__(self):
		s = '%(frequency)s, starting %(start)s'
		if self.interval > 1:
			s = s + '%(interval)d-'
		return s % {'frequency': self.get_frequency_display(),
					'start': self.schedule.start_date,
					'interval': self.interval}
