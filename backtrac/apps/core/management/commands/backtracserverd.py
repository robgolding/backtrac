from django.core.management.base import BaseCommand, CommandError

from twisted.internet import reactor

class Command(BaseCommand):
    help = 'Starts the backtrac server daemon (backtracserverd)'

    def handle(self, *args, **options):
        from backtrac.server import BackupServer
        server = BackupServer()
        server.start()
        reactor.run()
