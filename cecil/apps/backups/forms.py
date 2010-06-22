import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.datastructures import SortedDict

SECS_PER_DAY=3600*24

class TimedeltaFormField(forms.Field):
	default_error_messages = {
		'invalid':  _(u'Enter a whole number.'),
	}
	
	def __init__(self, *args, **kwargs):
		defaults={'widget': TimedeltaWidget}
		defaults.update(kwargs)
		super(TimedeltaFormField, self).__init__(*args, **defaults)
	
	def clean(self, value):
		# value comes from Timedelta.Widget.value_from_datadict(): tuple of strings
		super(TimedeltaFormField, self).clean(value)
		assert len(value)==len(self.widget.inputs), (value, self.widget.inputs)
		i = 0
		for value, multiply in zip(value, self.widget.multiply):
			try:
				i += (int(value) * multiply)
			except ValueError, TypeError:
				raise forms.ValidationError(self.error_messages['invalid'])
		return i

class TimedeltaWidget(forms.Widget):
	
	INPUTS = SortedDict()
	INPUTS['days'] = ([(i,i) for i in range(0,31)], 60*60*24)
	INPUTS['hours'] = ([(i,i) for i in range(0,24)], 60*60)
	INPUTS['minutes'] = ([(i,i) for i in range(0,60)], 60)
	INPUTS['seconds'] = ([(i,i) for i in range(0,60)], 1)
	
	def __init__(self, attrs=None):
		self.widgets = []
		if not attrs:
			attrs = {}
		multiply = []
		for input in self.INPUTS:
			self.widgets.append(forms.Select(attrs=attrs, choices=self.INPUTS[input][0]))
			multiply.append(self.INPUTS[input][1])
		self.inputs = self.INPUTS
		self.multiply = multiply
		super(TimedeltaWidget, self).__init__(attrs)
	
	def render(self, name, value, attrs):
		if value is None:
			values = [0 for i in self.inputs]
		elif isinstance(value, datetime.timedelta):
			values = split_seconds((value.days * SECS_PER_DAY) + value.seconds).values()
			print values
		elif isinstance(value, int):
			values = split_seconds(value).values()
		else:
			values = value
		
		id=attrs.pop('id')
		rendered = []
		for input, widget, val in zip(self.inputs, self.widgets, values):
			rendered.append(u'%s %s' % (_(input), 
				widget.render('%s_%s' % (name, input), val,))
			)
		return mark_safe('<div id="%s">%s</div>' % (id, ' '.join(rendered)))
	
	def value_from_datadict(self, data, files, name):
		# Don't throw ValidationError here, just return a tuple of strings.
		ret=[]
		for input, multi in zip(self.inputs, self.multiply):
			ret.append(data.get(u'%s_%s' % (name, input), 0))
		return tuple(ret)
	
	def _has_changed(self, initial_value, data_value):
		# data_value comes from value_from_datadict(): A tuple of strings.
		assert isinstance(initial_value, datetime.timedelta), initial_value
		initial=tuple([unicode(i) for i in split_seconds(initial_value.days*SECS_PER_DAY+initial_value.seconds).values()])
		assert len(initial)==len(data_value)
		#assert False, (initial, data_value)
		return bool(initial!=data_value)

def split_seconds(secs):
	ret = SortedDict()
	for input, val in TimedeltaWidget.INPUTS.items():
		_, multi = val
		count, secs = divmod(secs, multi)
		ret[input] = count
	return ret
