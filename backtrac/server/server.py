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
from twisted.internet.task import LoopingCall
from twisted.internet import defer

from django.conf import settings

from backtrac.server.storage import Storage
from backtrac.api.client import Client, get_client
from backtrac.utils.transfer import PageCollector, TransferPager

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
    def __init__(self, ip='0.0.0.0', port=8123):
        self.port = port
        self.clients = {}
        self.storage = Storage(settings.BACKTRAC_BACKUP_ROOT)

        realm = BackupRealm()
        realm.server = self
        checker = BackupClientAuthChecker()
        self.portal = portal.Portal(realm, [checker])
        self.factory = PBServerFactory(self.portal)
        self.service = TCPServer(self.port, self.factory, interface=ip)
        self.restore_loop = LoopingCall(self.execute_pending_restores)
        self.restore_loop.start(5)

    def execute_pending_restores(self):
        for hostname, client in self.clients.items():
            client.execute_pending_restores()

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

class BackupClient(pb.Avatar):
    def __init__(self, client_api, server):
        self.api = client_api
        self.server = server

    def attached(self, mind):
        self.remote = mind
        self.server.clients[self.api.get_hostname()] = self
        self.api.connected()
        print 'Client \'%s\' connected' % self.api.get_hostname()

    def detached(self, mind):
        self.remote = None
        del self.server.clients[self.api.get_hostname()]
        self.api.disconnected()
        print 'Client \'%s\' disconnected' % self.api.get_hostname()

    def perspective_get_paths(self):
        return self.api.get_paths()

    def perspective_get_present_state(self, path):
        return self.api.get_present_state(path)

    def perspective_check_file(self, path, mtime, size):
        if not self.api.is_excluded(path):
            return self.api.backup_required(path, mtime, size)
        return False

    def perspective_create_item(self, path, type):
        if not self.api.is_excluded(path):
            self.api.create_item(path, type)

    def perspective_delete_item(self, path):
        if not self.api.is_excluded(path):
            self.api.delete_item(path)

    def perspective_put_file(self, path, mtime, size):
        version_id, fdst = self.server.storage.put(self.api.get_hostname(),
                                                   path)
        collector = PageCollector(fdst)
        self.api.update_item(path, mtime, size, version_id)
        return collector

    def restore_file(self, restore_id, path, version_id):
        def _restore(collector, path, version_id):
            fd = self.server.storage.get(self.api.get_hostname(), path,
                                         version_id)
            pager = TransferPager(collector, fd)
            pager.wait()
            print 'Restore %d complete' % restore_id
            self.api.restore_complete(restore_id)

        print 'Restoring %s to %s (job %d)' % (path, self.api.get_hostname(),
                                               restore_id)
        self.api.restore_begin(restore_id)
        d = self.remote.callRemote('put_file', path)
        d.addCallback(_restore, path, version_id)

    def execute_pending_restores(self):
        jobs = self.api.get_pending_restore_jobs()
        for id, path, version_id in jobs:
            self.restore_file(id, path, version_id)
