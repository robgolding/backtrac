import datetime
from dateutil import rrule

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext, ugettext_lazy as _

import managers

FREQUENCY_CHOICES = (
	('YEARLY', _('Years')),
	('MONTHLY', _('Months')),
	('WEEKLY', _('Weeks')),
	('DAILY', _('Days')),
	('HOURLY', _('Hours')),
	('MINUTELY', _('Minutes'))
)

DEFAULT_FREQUENCY = rrule.MONTHLY

class Schedule(models.Model):
	"""
	Model to represent a schedule, which consists of a start date and multiple
	'rules' - each of which determines how often the given event recurs.
	"""
	start_date = models.DateField(_('start date'))
	start_time = models.TimeField(_('start time'))
	
	objects = managers.ScheduleManager()
	
	def get_start_datetime(self):
		return datetime.datetime.combine(self.start_date, self.start_time)
	
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
		try:
			frequency = eval('rrule.%s' % self.frequency)
		except:
			frequency = DEFAULT_FREQUENCY
		return rrule.rrule(frequency, interval=self.interval,
					dtstart=self.schedule.get_start_datetime())
	
	def get_next_occurrence(self):
		return self.get_rrule_object().after(datetime.datetime.now())
	
	def __unicode__(self):
		s = '%(frequency)s, starting %(start)s'
		if self.interval > 1:
			s = s + '%(interval)d-'
		return s % {'frequency': self.get_frequency_display(),
					'start': self.schedule.start_date,
					'interval': self.interval}
