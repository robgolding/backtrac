"""
Tests for the `catalog' application.
"""
import uuid, random

from django.test import TestCase

from backtrac.apps.clients.models import Client
from models import Item, Version

#TODO: Write a test for the download_version view

class ItemGetNameTest(TestCase):
    def setUp(self):
        """
        Create a single client and two items within that client - a file and
        a directory.
        """
        c = Client.objects.create(hostname='testclient', secret_key='')
        self.item_file = Item.objects.create(client=c, name='file', type='f')
        self.item_dir = Item.objects.create(client=c, name='dir', type='d')

    def test_dir_get_name(self):
        """Test that the directory name ends in a slash"""
        self.assertTrue(self.item_dir.get_name().endswith('/'))

    def test_file_get_name(self):
        """Test that the file name doesn't end in a slash"""
        self.assertFalse(self.item_file.get_name().endswith('/'))

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
        self.client = Client.objects.create(hostname='test',
                                            secret_key='')
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
        self.assertEqual(self.item.get_last_modified_version().id,
                             self.version.id)
        self.assertEqual(self.item.get_last_modified_version().item,
                             self.version.item)
        self.assertEqual(self.item.get_last_modified_version().mtime,
                             self.version.mtime)
        self.assertEqual(self.item.get_last_modified_version().size,
                             self.version.size)
