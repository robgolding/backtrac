from django.db import models

class DataManager(models.Manager):
    """
    A manager for the data object, providing convenience methods to make
    visualisation easier.
    """
    def average(self, from_timestamp=None, to_timestamp=None):
        """
        Average the value of all the data points that occur in between
        from_timestamp and to_timestamp.
        """
        query = {}
        if from_timestamp is not None:
            query['timestamp__gte'] = from_timestamp
        if to_timestamp is not None:
            query['timestamp__lte'] = to_timestamp
        qs = self.get_query_set().filter(**query)
        avg = qs.aggregate(avg=models.Avg('value'))['avg']
        return avg

class DataType(models.Model):
    """A data type is a 'key' with which to identify time-series data."""
    name = models.CharField(max_length=255, db_index=True)

    def __unicode__(self):
        return self.name

class Data(models.Model):
    """
    A time series data point of a given type. Stores the value and the time
    at which it was recorded.
    """
    type = models.ForeignKey(DataType, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    value = models.BigIntegerField()

    objects = DataManager()

    def __unicode__(self):
        return '%s, %s, %s' % (self.type, self.timestamp, self.value)
