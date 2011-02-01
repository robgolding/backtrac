import sys
import os

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
        ('port', 'p', None, 'The port to listen on', int),
    )
    
    def postOptions(self):
        if not self['port']:
            raise usage.UsageError

class ServerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracweb'
    description = 'Backtrac Web Interface'
    options = Options

    def wsgi_resource(self):
        pool = threadpool.ThreadPool()
        pool.start()
        reactor.addSystemEventTrigger('after', 'shutdown', pool.stop)
        wsgi_resource = wsgi.WSGIResource(reactor, pool, WSGIHandler())
        return wsgi_resource

    def makeService(self, options):
        application = service.Application('backtracweb')
        site = server.Site(self.wsgi_resource())
        svc = internet.TCPServer(options['port'], site)
        svc.setServiceParent(application)
        return svc

serviceMaker = ServerServiceMaker()
