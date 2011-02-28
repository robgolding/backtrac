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
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

class Options(usage.Options):
    optParameters = (
        ('config', '', '/etc/backtrac/backtracserverd.conf',
         'Config file', str),
    )

class Root(resource.Resource):
    def __init__(self, wsgi_resource):
        resource.Resource.__init__(self)
        self.wsgi_resource = wsgi_resource

    def getChild(self, path, request):
        path0 = request.prepath.pop(0)
        request.postpath.insert(0, path0)
        return self.wsgi_resource

class ThreadPoolService(service.Service):
    def __init__(self, pool):
        self.pool = pool

    def startService(self):
        service.Service.startService(self)
        self.pool.start()

    def stopService(self):
        service.Service.stopService(self)
        self.pool.stop()

class ServerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = 'backtracweb'
    description = 'Backtrac web server'
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
            port = cp.getint('backtracweb', 'listen_port')
            #application = service.Application('backtracweb')

            # make a new MultiService to hold the thread/web services
            multi = service.MultiService()

            # make a new ThreadPoolService and add it to the multi service
            tps = ThreadPoolService(threadpool.ThreadPool())
            tps.setServiceParent(multi)

            # create the WSGI resource using the thread pool and Django handler
            resource = wsgi.WSGIResource(reactor, tps.pool, WSGIHandler())
            # create a custom 'root' resource, that we can add other things to
            root = Root(resource)

            # serve the static media
            static_resource = static.File(settings.STATIC_ROOT)
            root.putChild(settings.STATIC_URL.strip('/'), static_resource)

            # create the site and a TCPServer service to serve it with
            site = server.Site(root)
            ws = internet.TCPServer(port, site)

            # add the web server service to the multi service
            ws.setServiceParent(multi)

            return multi
        except ConfigParser.Error:
            print >> sys.stderr, 'Error parsing config file:', config
            sys.exit(1)

serviceMaker = ServerServiceMaker()
