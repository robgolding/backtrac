import os

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

os.environ['DJANGO_SETTINGS_MODULE'] = 'backtrac.settings'

from backtrac.server import BackupServer

class Options(usage.Options):
    optParameters = (
        ('port', 'p', None, 'The port to listen on', int),
    )
    
    def postOptions(self):
        if not self['port']:
            raise usage.UsageError

class ServerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracserverd'
    description = 'Backtrac Server Daemon'
    options = Options

    def makeService(self, options):
        server = BackupServer(port=options['port'])
        return server.service

serviceMaker = ServerServiceMaker()
