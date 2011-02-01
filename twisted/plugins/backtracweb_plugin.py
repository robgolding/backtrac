import os
import sys
import ConfigParser

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import internet, service
from twisted.application.service import IServiceMaker
from twisted.web import server, resource, wsgi, static, client
from twisted.python import threadpool
from twisted.internet import reactor, defer

os.environ['DJANGO_SETTINGS_MODULE'] = 'backtrac.settings'
from django.core.handlers.wsgi import WSGIHandler

class Options(usage.Options):
    optParameters = (
        ('config', '', '/etc/backtrac/backtracserverd.conf',
         'Config file', str),
    )

class ServerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracweb'
    description = 'Backtrac Web Interface'
    options = Options

    def getConfig(self, config_file):
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read(config_file)
        except:
            print >> sys.stderr, 'Error reading config file:', config_file
            sys.exit(1)
        return cp


    def wsgi_resource(self):
        pool = threadpool.ThreadPool()
        pool.start()
        reactor.addSystemEventTrigger('after', 'shutdown', pool.stop)
        wsgi_resource = wsgi.WSGIResource(reactor, pool, WSGIHandler())
        return wsgi_resource

    def makeService(self, options):
        config = options['config']
        cp = self.getConfig(config)
        try:
            port = cp.getint('backtracweb', 'listen_port')
            application = service.Application('backtracweb')
            site = server.Site(self.wsgi_resource())
            svc = internet.TCPServer(port, site)
            svc.setServiceParent(application)
            return svc
        except ConfigParser.Error:
            print >> sys.stderr, 'Error parsing config file:', config
            sys.exit(1)

serviceMaker = ServerServiceMaker()
