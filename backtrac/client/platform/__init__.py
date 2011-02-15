import sys

if sys.platform == 'linux2':
    import linux as source
else:
    import other as source

FileSystemMonitor = source.FileSystemMonitor
