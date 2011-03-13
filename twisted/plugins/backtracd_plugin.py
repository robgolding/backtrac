import sys
import ConfigParser

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from backtrac.client.broker import BackupBroker
from backtrac.client import BackupClient

class Options(usage.Options):
    optParameters = (
        ('config', '', '/etc/backtrac/client.conf',
         'Config file', str),
    )

class ClientServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracd'
    description = 'Backtrac client'
    options = Options

    def getConfig(self, config_file):
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read(config_file)
        except:
            print >> sys.stderr, 'Error reading config file:', config_file
            sys.exit(1)
        return cp

    def makeService(self, options):
        config = options['config']
        cp = self.getConfig(config)
        try:
            server = cp.get('backtracd', 'server')
            port = cp.getint('backtracd', 'port')
            secrey_key = cp.get('backtracd', 'secret_key')
            broker = BackupBroker(server=server, port=port,
                                  secret_key=secrey_key)
            client = BackupClient(broker)
            client.start()
            return broker.service
        except ConfigParser.Error:
            raise
            print >> sys.stderr, 'Error parsing config file:', config
            sys.exit(1)

serviceMaker = ClientServiceMaker()
