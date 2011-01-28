from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from twisted.internet import reactor

class Command(BaseCommand):
    args = '<server> <port> <secret key>'
    help = 'Starts the backtrac client daemon (backtracd)'

    def handle(self, *args, **options):
        from backtrac.client import BackupClient
        client = BackupClient(server=args[0], port=int(args[1]),
                              secret_key=args[2])
        client.connect(True)
        reactor.run()
