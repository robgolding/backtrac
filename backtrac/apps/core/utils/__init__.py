import os

from django.conf import settings

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def check_daemon_status(q):
    from twisted import cred
    from twisted.spread import pb
    from twisted.internet import reactor

    from backtrac.client import BackupClient

    def _connected(perspective):
        q.put(True)
        reactor.stop()

    def _error(error):
        q.put(False)
        reactor.stop()

    client = BackupClient(server='localhost', secret_key=settings.SECRET_KEY)

    factory = pb.PBClientFactory()
    reactor.connectTCP('localhost', 8123, factory)
    d = factory.login(
        cred.credentials.UsernamePassword(
            'localhost',
            settings.SECRET_KEY
        ),
        client=client
    )
    d.addCallback(_connected)
    d.addErrback(_error)

    reactor.run()
