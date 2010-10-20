from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Starts the backtrac server daemon (backtracd)'

    def handle(self, *args, **options):
        from backtrac.server import BackupServer
        server = BackupServer()
        server.start()
