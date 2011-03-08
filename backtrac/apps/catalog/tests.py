"""
Tests for the `catalog' application.
"""
import os
import uuid
import shutil
import random

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth.models import User

from backtrac.server.storage import Storage
from backtrac.apps.clients.models import Client
from backtrac.apps.catalog.models import Item, Version, RestoreJob, \
        get_or_create_item

class ItemPathTest(TestCase):
    def setUp(self):
        """
        """
        self.client = Client.objects.create(hostname='test', secret_key='')
        self.item1 = Item.objects.create(client=self.client,
                                         name='home',
                                         type='d')
        self.item2 = Item.objects.create(client=self.client,
                                         name='test',
                                         parent=self.item1,
                                         type='d')
        self.item3 = Item.objects.create(client=self.client,
                                         name='file',
                                         parent=self.item2,
                                         type='f')

    def test_item_path(self):
        """
        Test that the created items are given the correct path attribute
        automatically, via the update_item pre-save signal.
        """
        self.assertEqual(self.item1.path, '/home')
        self.assertEqual(self.item2.path, '/home/test')
        self.assertEqual(self.item3.path, '/home/test/file')

class ItemLatestVersionTest(TestCase):
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

class BrowseRouteTest(TestCase):
    def setUp(self):
        """
        Create a test user, and an Item to retrieve with the browse_route view.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.client_obj = Client.objects.create(hostname='test', secret_key='')
        self.item, _ = get_or_create_item(self.client_obj, '/test/item', 'f')
        self.version = Version.objects.create(id=str(uuid.uuid4()),
                                              item=self.item, mtime=123,
                                              size=456)

    def test_browse_route_view_file(self):
        """
        Test that the browse_route view returns a response with the correct
        context when viewing a file.
        """
        self.client.login(username='test', password='test')

        response = self.client.get(self.item.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['item'], self.item)
        self.assertEqual(list(response.context['versions']), [self.version])

    def test_browse_route_browse_directory(self):
        """
        Test that the browse_route view returns a response with the correct
        context when browsing a directory.
        """
        self.client.login(username='test', password='test')

        response = self.client.get(self.item.parent.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['item'], self.item.parent)
        self.assertEqual(list(response.context['item'].children.all()),
                         list(self.item.parent.children.all()))

class DownloadVersionTest(TestCase):
    FILE_CONTENTS = "This is a test file"

    def setUp(self):
        """
        Create a test user, item and version, then put a file into the storage
        system for that version.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.client_obj = Client.objects.create(hostname='test', secret_key='')
        self.item, _ = get_or_create_item(self.client_obj, '/test/item', 'f')
        self.version = Version.objects.create(id=str(uuid.uuid4()),
                                              item=self.item, mtime=123,
                                              size=456)

        self.storage = Storage(settings.BACKTRAC_BACKUP_ROOT)

        _, fd = self.storage.put(self.client_obj.hostname, self.item.path,
                                 self.version.id)
        fd.write(self.FILE_CONTENTS)
        fd.close()

    def test_download_version(self):
        """
        Test that the download_version view returns the correct file from the
        storage subsystem.
        """
        self.client.login(username='test', password='test')

        response = self.client.get(reverse('catalog_download_version',
                                           args=[self.version.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.FILE_CONTENTS)

    def tearDown(self):
        """
        Remove the test storage directory we created earlier.
        """
        shutil.rmtree(settings.BACKTRAC_BACKUP_ROOT)

class RestoreVersionTest(TestCase):
    FILE_CONTENTS = "This is a test file, ready to be restored"
    RESTORE_PATH = os.path.join(settings.BACKTRAC_TMP_DIR, 'restore-%s'
                                % str(uuid.uuid4()))

    def setUp(self):
        """
        Create a test user, item and version, then put a file into the storage
        system for that version.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.client_obj = Client.objects.create(hostname='test', secret_key='')
        self.item, _ = get_or_create_item(self.client_obj, self.RESTORE_PATH, 'f')
        self.version1 = Version.objects.create(id=str(uuid.uuid4()),
                                               item=self.item, mtime=123,
                                               size=456)
        self.version2 = Version.objects.create(id=str(uuid.uuid4()),
                                               item=self.item, mtime=123,
                                               size=456,
                                               restored_from=self.version1)

        self.storage = Storage(settings.BACKTRAC_BACKUP_ROOT)

        _, fd = self.storage.put(self.client_obj.hostname, self.item.path,
                                 self.version1.id)
        fd.write(self.FILE_CONTENTS)
        fd.close()

    def test_restore_version(self):
        """
        Test that the restore_version view creates a RestoreJob object with the
        correctly resolved version ID, and returns a 302 redirect status code.
        """
        self.client.login(username='test', password='test')

        response = self.client.get(reverse('catalog_restore_version',
                                           args=[self.version2.id]))

        self.assertEqual(response.status_code, 302)

        restore_job = RestoreJob.objects.get(client=self.client_obj)

        self.assertEqual(restore_job.version.id, self.version1.id)

    def tearDown(self):
        """
        Remove the test storage directory we created earlier.
        """
        shutil.rmtree(settings.BACKTRAC_BACKUP_ROOT)
