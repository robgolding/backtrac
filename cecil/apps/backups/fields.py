import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

import forms

SECS_PER_DAY=3600*24

class PrettyTimedelta(datetime.timedelta):
	
	def __unicode__(self):
		values = forms.split_seconds((self.days * SECS_PER_DAY) + self.seconds)
		ret = 'every'
		for key, val in values.items():
			if val:
				ret += ' %s %s,' % (val, key)
		return ret.strip(', ')

class TimedeltaField(models.Field):
	"""
	Store Python's datetime.timedelta in an integer column.
	Most databasesystems only support 32 Bit integers by default.
	"""
	__metaclass__ = models.SubfieldBase
	
	def __init__(self, *args, **kwargs):
		super(TimedeltaField, self).__init__(*args, **kwargs)
	
	def to_python(self, value):
		if (not value):
			return datetime.timedelta(0)
		if isinstance(value, datetime.timedelta):
			return value
		assert isinstance(value, (int, long,) ), (value, type(value))
		return PrettyTimedelta(seconds=value)
	
	def get_internal_type(self):
		return 'IntegerField'
	
	def get_prep_value(self, value):
		if (value is None) or isinstance(value, int):
			return value
		else:
			return (SECS_PER_DAY * value.days) + value.seconds
	
	def formfield(self, *args, **kwargs):
		defaults={'form_class': forms.TimedeltaFormField}
		defaults.update(kwargs)
		return super(TimedeltaField, self).formfield(*args, **defaults)
