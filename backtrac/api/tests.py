"""
Tests for the internal API.
"""

from django.test import TestCase

from backtrac.apps.core.models import GlobalExclusion
from backtrac.apps.clients.models import Client, Exclusion
from backtrac.api import client

class ExclusionsTest(TestCase):
    def setUp(self):
        """
        Create some global exclusions, and a test client with some local
        exclusions. Then create a test API instance to use later on.
        """
        GlobalExclusion.objects.create(glob='*.txt')
        GlobalExclusion.objects.create(glob='.*.swp')

        self.client = Client.objects.create(hostname='test', secret_key='')
        Exclusion.objects.create(client=self.client, glob='*.tmp')

        self.api = client.Client(self.client)

    def test_file_exclusions(self):
        """
        Test that files are excluded correctly with both the global exclusions
        and the local client exclusions.
        """
        self.assertEqual(self.api.is_excluded('file.txt'), True)
        self.assertEqual(self.api.is_excluded('.test.py.swp'), True)

        self.assertEqual(self.api.is_excluded('document.pdf'), False)
        self.assertEqual(self.api.is_excluded('test.txt.bak'), False)

        self.assertEqual(self.api.is_excluded('.temp_file.tmp'), True)
        self.assertEqual(self.api.is_excluded('temoporary.tmp.lst'), False)
