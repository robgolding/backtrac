import os, random

from zope.interface import implements

from twisted.python import failure, log
from twisted.internet import reactor
from twisted.cred import portal, checkers, error, credentials
from twisted.spread import pb
from twisted.spread.pb import PBServerFactory 

from twisted.spread.util import FilePager
from twisted.internet import defer

from utils import PageCollector, get_storage_for

from backtrac.apps.clients.models import Client
from backtrac.apps.catalog.models import Item, Version, get_or_create_item

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
        try:
            client = Client.objects.get(hostname=credentials.username)
            return defer.maybeDeferred(
                credentials.checkPassword,
                client.secret_key).addCallback(self._passwordMatch, client)
        except Client.DoesNotExist:
            return defer.fail(error.UnauthorizedLogin())

class BackupServer(object):
    def __init__(self, port=8123):
        self.port = port

    def start(self):
        realm = BackupRealm()
        realm.server = self
        checker = BackupClientAuthChecker()
        p = portal.Portal(realm, [checker])

        reactor.listenTCP(self.port, PBServerFactory(p))
        print 'Listening on port %d' % self.port
        reactor.run()

class BackupRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self, client_id, mind, *interfaces):
        assert pb.IPerspective in interfaces
        client_obj = Client.objects.get(hostname=client_id)
        avatar = BackupClient(client_obj, self.server)
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)

class BackupClient(pb.Avatar):
    def __init__(self, client, server):
        self.client = client
        self.server = server
        self.storage = get_storage_for(client)

    def attached(self, mind):
        self.remote = mind
        print 'Client %d (%s) connected' % (self.client.pk,
                                            self.client.hostname)

    def detached(self, mind):
        self.remote = None
        print 'Client %d (%s) disconnected' % (self.client.pk,
                                            self.client.hostname)

    def perspective_get_paths(self):
        return [p.path for p in self.client.filepaths.all()]

    def perspective_check_file(self, path, mtime, size):
        item, created = get_or_create_item(self.client, path, 'f')
        versions = item.versions.all()
        if not versions:
            return True
        version = versions.latest()
        if mtime == version.mtime and size == version.size:
            return False
        return True

    def perspective_put_file(self, path, mtime, size):
        item, created = get_or_create_item(self.client, path, 'f')
        version_id, fdst = self.storage.add(path)
        collector = PageCollector(fdst)
        version, _ = Version.objects.get_or_create(id=version_id,
                                         item=item, mtime=mtime, size=size)
        return collector

if __name__ == '__main__':
    server = BackupServer()
    server.start()
