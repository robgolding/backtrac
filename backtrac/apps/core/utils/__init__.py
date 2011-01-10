import os

from django.conf import settings

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def run_in_process(func, args=[]):
    from multiprocessing import Process, Queue

    q = Queue()
    args = [q] + args
    p = Process(target=func, args=args)
    p.start()
    p.join()
    result = q.get()
    if isinstance(result, Exception):
        raise result
    return result

def get_server_status(q):
    from twisted import cred
    from twisted.spread import pb
    from twisted.internet import reactor

    from backtrac.client import BackupClient

    def _error(error):
        q.put(False)
        reactor.stop()

    def _connected(perspective):
        q.put(True)
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

def call_remote_method(q, method):
    from twisted import cred
    from twisted.spread import pb
    from twisted.internet import reactor

    from backtrac.client import BackupClient

    def _error(error):
        q.put(error)
        reactor.stop()

    def _connected(perspective):
        perspective.callRemote(method).addCallbacks(_result, _error)

    def _result(result):
        q.put(result)
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

def num_clients():
    return run_in_process(call_remote_method, ['num_clients',])

def server_status():
    return run_in_process(get_server_status)
