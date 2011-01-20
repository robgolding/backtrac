"""
Tests for the `catalog' application.
"""
import uuid, random

from django.test import TestCase

from backtrac.apps.clients.models import Client
from models import Item, Version

#TODO: Write a test for the download_version view

class LatestVersionTest(TestCase):
    def _add_version_to_item(self, item):
        """
        Stick another version onto the given item with a new UUID, and a
        random mtime and size - then return it.
        """
        uid = str(uuid.uuid4())
        mtime = random.randrange(123, 12345)
        size = random.randrange(123, 12345)
        return Version.objects.create(id=uid, item=item,
                                   mtime=23456, size=23456)

    def setUp(self):
        """
        Create a single client and a single item within that client. Then, add
        10 new versions to that item.
        """
        self.client = Client.objects.create(hostname='test', secret_key='')
        self.item = Item.objects.create(client=self.client,
                                        name='test',
                                        type='f')
        for i in range(10):
            self.version = self._add_version_to_item(self.item)

    def test_latest_version(self):
        """
        Test that the returned 'latest' version is the last one that was
        added.
        """
        self.assertEqual(self.item.latest_version.id,
                             self.version.id)
        self.assertEqual(self.item.latest_version.item,
                             self.version.item)
        self.assertEqual(self.item.latest_version.mtime,
                             self.version.mtime)
        self.assertEqual(self.item.latest_version.size,
                             self.version.size)

class GetOrCreateItemTest(TestCase):
    def setUp(self):
        """
        Create a client to use within the test.
        """
        self.client = Client.objects.create(hostname='test', secret_key='')
        self.path = '/testing/get/or/create/item'
        self.type = 'f'

    def test_get_or_create_item(self):
        """
        Test that catalog.models.get_or_create_item works as expected.
        """
        from backtrac.apps.catalog.models import get_or_create_item

        item, created = get_or_create_item(self.client, self.path, self.type)

        self.assertEqual(created, True)
        self.assertEqual(item.path, self.path)
        self.assertEqual(item.type, self.type)
        self.assertEqual(item.client.pk, self.client.pk)
        self.assertEqual(item.client.hostname, self.client.hostname)
