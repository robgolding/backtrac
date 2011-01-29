from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from backtrac.client import BackupBroker, BackupClient

class Options(usage.Options):
    optParameters = (
        ('server', 's', None, 'The server to connect to', str),
        ('port', 'p', None, 'The port to connect to the server on', int),
        ('secret-key', 'k', None, 'The secret key to authenticate with', str),
    )
    
    def postOptions(self):
        if not self['server'] or not self['port'] or not self['secret-key']:
            raise usage.UsageError

class ClientServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracd'
    description = 'Backtrac Client Daemon'
    options = Options

    def makeService(self, options):
        def makeClient(broker):
            BackupClient(broker).start()
        broker = BackupBroker(server=options['server'], port=options['port'],
                              secret_key=options['secret-key'])
        broker.connect().addCallback(makeClient)
        return broker.service

serviceMaker = ClientServiceMaker()
