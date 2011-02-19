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

from backtrac.server.storage import Storage, ClientStorage
from backtrac.apps.clients import models as clients
from backtrac.apps.catalog import models as catalog
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
                                                 'localhost')
        try:
            client = clients.Client.objects.get(hostname=credentials.username)
            return defer.maybeDeferred(
                credentials.checkPassword,
                client.secret_key).addCallback(self._passwordMatch,
                                               client.hostname)
        except clients.Client.DoesNotExist:
            return defer.fail(error.UnauthorizedLogin())

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

    def requestAvatar(self, client_id, mind, *interfaces):
        assert pb.IPerspective in interfaces
        if client_id == 'localhost':
            avatar = ManagementClient(self.server)
        else:
            client_obj = clients.Client.objects.get(hostname=client_id)
            avatar = BackupClient(client_obj, self.server)
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

class BackupClient(pb.Avatar):
    def __init__(self, client, server):
        self.client = client
        self.server = server
        storage = Storage(settings.BACKTRAC_BACKUP_ROOT)
        self.storage = ClientStorage(storage, client)

    def attached(self, mind):
        self.remote = mind
        self.server.clients.append(self)
        clients.client_connected.send(sender=self, client=self.client)
        print 'Client \'%s\' connected' % self.client.hostname

    def detached(self, mind):
        self.remote = None
        self.server.clients.remove(self)
        clients.client_disconnected.send(sender=self, client=self.client)
        print 'Client \'%s\' disconnected' % self.client.hostname

    def perspective_get_paths(self):
        return [p.path for p in self.client.filepaths.all()]

    def perspective_get_present_state(self, path):
        def get_children(item, items):
            items.append(item.path)
            for i in item.children.present():
                get_children(i, items)
        items = []
        try:
            item = catalog.Item.objects.get(client=self.client, path=path)
            get_children(item, items)
        except catalog.Item.DoesNotExist:
            pass
        return items

    def perspective_check_file(self, path, mtime, size):
        try:
            item = catalog.Item.objects.get(client=self.client, path=path)
            if not item.latest_version or item.deleted:
                return True
            if abs(mtime - item.latest_version.mtime) < 1:
                if abs(size - item.latest_version.size) < 1:
                    return False
        except catalog.Item.DoesNotExist:
            pass
        return True

    def perspective_create_item(self, path, type):
        catalog.item_created.send(sender=self, path=path, type=type,
                                  client=self.client)

    def perspective_delete_item(self, path):
        catalog.item_deleted.send(sender=self, path=path, client=self.client)

    def perspective_put_file(self, path, mtime, size):
        version_id, fdst = self.storage.add(path)
        collector = PageCollector(fdst)
        catalog.item_updated.send(sender=self, path=path, mtime=mtime,
                                  size=size, client=self.client,
                                  version_id=version_id)
        return collector

if __name__ == '__main__':
    server = BackupServer()
    server.start()
