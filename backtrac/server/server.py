import os
import random
import datetime

from zope.interface import implements

from twisted.python import failure, log
from twisted.internet import reactor
from twisted.cred import portal, checkers, error, credentials
from twisted.spread import pb
from twisted.spread.pb import PBServerFactory
from twisted.application.service import Application
from twisted.application.internet import TCPServer
from twisted.spread.util import FilePager
from twisted.internet import defer

from django.conf import settings

from backtrac.api.client import Client, get_client
from backtrac.utils.transfer import PageCollector

class BackupClientAuthChecker:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def _passwordMatch(self, matched, client):
        if matched:
            return client
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, credentials):
        if credentials.username == 'localhost':
            return defer.maybeDeferred(
                credentials.checkPassword,
                settings.SECRET_KEY).addCallback(self._passwordMatch,
                                                 None)
        client = get_client(credentials.username)
        if client is None:
            return defer.fail(error.UnauthorizedLogin())
        return defer.maybeDeferred(
            credentials.checkPassword,
            client.get_key()).addCallback(self._passwordMatch,
                                           client)

class BackupServer(object):
    def __init__(self, port=8123):
        self.port = port
        self.clients = []

        realm = BackupRealm()
        realm.server = self
        checker = BackupClientAuthChecker()
        self.portal = portal.Portal(realm, [checker])
        self.factory = PBServerFactory(self.portal)
        self.service = TCPServer(self.port, self.factory)

    def start(self):
        self.service.startService()

class BackupRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self, client_api, mind, *interfaces):
        assert pb.IPerspective in interfaces
        if client_api is not None:
            avatar = BackupClient(client_api, self.server)
        else:
            avatar = ManagementClient(self.server)
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)

class ManagementClient(pb.Avatar):
    def __init__(self, server):
        self.server = server

    def attached(self, mind):
        self.remote = mind

    def detached(self, mind):
        self.remote = None

    def perspective_num_clients(self):
        return len(self.server.clients)

    def perspective_restore_file(self, client, version_id):
        pass

class BackupClient(pb.Avatar):
    def __init__(self, client_api, server):
        self.api = client_api
        self.server = server
        self.storage = client_api.get_storage()

    def attached(self, mind):
        self.remote = mind
        self.server.clients.append(self)
        self.api.connected()
        print 'Client \'%s\' connected' % self.api.get_hostname()

    def detached(self, mind):
        self.remote = None
        self.server.clients.remove(self)
        self.api.disconnected()
        print 'Client \'%s\' disconnected' % self.api.get_hostname()

    def perspective_get_paths(self):
        return self.api.get_paths()

    def perspective_get_present_state(self, path):
        return self.api.get_present_state(path)

    def perspective_check_file(self, path, mtime, size):
        return self.api.backup_required(path, mtime, size)

    def perspective_create_item(self, path, type):
        return self.api.create_item(path, type)

    def perspective_delete_item(self, path):
        return self.api.delete_item(path)

    def perspective_put_file(self, path, mtime, size):
        version_id, fdst = self.storage.add(path)
        collector = PageCollector(fdst)
        self.api.update_item(path, mtime, size, version_id)
        return collector

if __name__ == '__main__':
    server = BackupServer()
    server.start()
