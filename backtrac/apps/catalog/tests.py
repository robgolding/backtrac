"""
Tests for the `catalog' application.
"""
import uuid

from django.test import TestCase

from backtrac.apps.clients.models import Client
from models import Item, Version

class LatestVersionTest(TestCase):
    def setUp(self):
        uid = str(uuid.uuid4())
        c = Client.objects.create(hostname='testclient', secret_key='')
        i = Item.objects.create(client=c, name='test', type='f')
        v = Version.objects.create(id=uid, item=i, mtime=12345, size=12345)
        self.item = i
        self.version = v

    def test_latest_version(self):
        """
        Tests that the latest version is correct.
        """
        self.failUnlessEqual(self.item.get_last_modified_version().id,
                             self.version.id)
