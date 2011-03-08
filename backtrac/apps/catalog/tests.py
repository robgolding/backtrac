"""
Tests for the `catalog' application.
"""
import uuid, random

from django.test import TestCase

from backtrac.apps.clients.models import Client
from backtrac.apps.catalog.models import Item, Version, get_or_create_item

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
        item, created = get_or_create_item(self.client, self.path, self.type)

        self.assertEqual(created, True)
        self.assertEqual(item.path, self.path)
        self.assertEqual(item.type, self.type)
        self.assertEqual(item.client.pk, self.client.pk)
        self.assertEqual(item.client.hostname, self.client.hostname)

class ItemCreatedTest(TestCase):
    def setUp(self):
        """
        Create a test client to use within the test.
        """
        self.client = Client.objects.create(hostname='test', secret_key='')
        self.path = '/testing/item/created/signal'
        self.sender = None # we don't need a specific sender in this case

    def test_item_created_signal(self):
        """
        Test that the catalog.models.item_created signal does not raise an
        IntegrityError if a directory and a file are created with the same
        path.
        """
        from backtrac.apps.catalog.models import item_created

        item_created.send(sender=None, path=self.path, type='f',
                          client=self.client)

        item_created.send(sender=None, path=self.path, type='d',
                          client=self.client)

class ResolveOriginalVersionTest(TestCase):
    def setUp(self):
        """
        Create an Item and a chain of versions to test the resolve_original()
        method on.
        """
        import uuid

        self.client = Client.objects.create(hostname='test', secret_key='')
        self.item, _ = get_or_create_item(self.client, '/test/item', 'f')

        self.versions = []
        self.original = Version.objects.create(id=str(uuid.uuid4()),
                                               item=self.item, mtime=123,
                                               size=456)
        v = self.original
        for i in range(5):
            v = Version.objects.create(id=str(uuid.uuid4()), item=self.item,
                                       mtime=123, size=456,
                                       restored_from=v)
            self.versions.append(v)

    def test_resolve_original(self):
        """
        Test that the resolve_original() method on the Version class works as
        expected.
        """
        for v in self.versions:
            self.assertEqual(v.resolve_original(), self.original)
