import datetime

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
