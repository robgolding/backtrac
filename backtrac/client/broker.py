import socket

from twisted.spread import pb
from twisted.spread.flavors import Referenceable
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.defer import Deferred
from twisted import cred

from twisted.application.internet import TCPClient

class BackupBroker(pb.Referenceable):
    def __init__(self, server='localhost', port=8123,
                 hostname=socket.gethostname(), secret_key=''):
        self.server = server
        self.port = port
        self.hostname = hostname
        self.secret_key = secret_key
        self.connected = False
        self.factory = pb.PBClientFactory()
        self.service = TCPClient(self.hostname, self.port, self.factory)

    def get_paths(self):
        return self.perspective.callRemote('get_paths')

    def get_present_state(self, path):
        return self.perspective.callRemote('get_present_state', path)

    def check_file(self, path, mtime, size):
        return self.perspective.callRemote('check_file', path, mtime, size)

    def delete_item(self, path):
        return self.perspective.callRemote('delete_item', path)

    def create_item(self, path, type='f'):
        return self.perspective.callRemote('create_item', path, type)

    def put_file(self, path, mtime, size):
        return self.perspective.callRemote('put_file', path, mtime, size)

    def login(self):
        return self.factory.login(
            cred.credentials.UsernamePassword(
                self.hostname,
                self.secret_key
            ),
            client=self
        )

    def connect(self):
        self.service.startService()
        d = Deferred()
        r = self.login()
        r.addCallbacks(self._logged_in, self._error)
        r.addCallback(lambda _: d.callback(self))
        return d

    def _logged_in(self, perspective):
        self.perspective = perspective
        self.connected = True

    def _error(self, error):
        if error.type == 'twisted.cred.error.UnauthorizedLogin':
            print >>sys.stderr, 'Failed to authenticate with server: %s' % self.server
        elif error.type == ConnectionRefusedError:
            print >>sys.stderr, 'Connection refused when connecting to server: %s' % self.server
        else:
            print >>sys.stderr, error.getTraceback()
