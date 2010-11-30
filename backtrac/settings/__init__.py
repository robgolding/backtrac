import sys

from default import *

try:
    from local import *
except ImportError:
    pass

if 'test' in sys.argv:
    try:
        from test import *
    except ImportError:
        pass
