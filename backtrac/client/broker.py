import sys
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

    def login(self, client):
        return self.factory.login(
            cred.credentials.UsernamePassword(
                self.hostname,
                self.secret_key
            ),
            client=client
        )

    def connect(self, client=None):
        self.service.startService()
        d = Deferred()
        r = self.login(client or self)
        r.addCallback(self._logged_in)
        r.addCallbacks(lambda _: d.callback(self), lambda x: d.errback(x))
        return d

    def _logged_in(self, perspective):
        self.perspective = perspective
        self.connected = True
