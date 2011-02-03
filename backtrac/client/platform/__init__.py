import sys

if sys.platform == 'linux2':
    import linux
    source = linux
else:
    import other
    source = other

FileSystemMonitor = source.FileSystemMonitor
