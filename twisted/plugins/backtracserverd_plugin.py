import os
import sys
import ConfigParser

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

os.environ['DJANGO_SETTINGS_MODULE'] = 'backtrac.settings'

from backtrac.server import BackupServer

class Options(usage.Options):
    optParameters = (
        ('config', '', '/etc/backtrac/server.conf',
         'Config file', str),
    )

class ServerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracserverd'
    description = 'Backtrac server'
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
            ip = cp.get('backtracserverd', 'listen_ip')
            port = cp.getint('backtracserverd', 'listen_port')
            server = BackupServer(ip=ip, port=port)
            return server.service
        except ConfigParser.Error:
            print >> sys.stderr, 'Error parsing config file:', config
            sys.exit(1)

serviceMaker = ServerServiceMaker()
