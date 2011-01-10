import os

from django.conf import settings

from twisted.spread.flavors import Referenceable

def get_storage_for(client):
    from backtrac.apps.clients.models import Client
    from backtrac.apps.core.storage import Storage, ClientStorage
    storage = Storage(settings.BACKTRAC_BACKUP_ROOT)
    return ClientStorage(storage, client)

class PageCollector(Referenceable):
    def __init__(self, fdst):
        self.fdst = fdst

    def remote_gotPage(self, page):
        self.fdst.write(page)

    def remote_endedPaging(self):
        self.fdst.close()
