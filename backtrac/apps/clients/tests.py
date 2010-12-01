"""
Tests for the `clients' application.
"""
from django.test import TestCase
from django.contrib.auth.models import User

from models import Client

class CreateClientTest(TestCase):
    def setUp(self):
        """
        Create a test user and record some test fields for use later on.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.hostname = 'test'
        self.secret_key = 'secret'

    def test_create_client_view(self):
        """
        Login using the test user, then POST to the create_client view. Check
        that the response code is OK and that the client has been created
        correctly.
        """
        self.client.login(username='test', password='test')

        response = self.client.post('/clients/create/', {
            'hostname': self.hostname,
            'secret_key': self.secret_key,
            'filepaths-TOTAL_FORMS': 0,
            'filepaths-INITIAL_FORMS': 0,
            'filepaths-MAX_NUM_FORMS': 0,
        }, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['object'].hostname, self.hostname)
        self.assertEqual(response.context['object'].secret_key, self.secret_key)

class UpdateClientTest(TestCase):
    def setUp(self):
        """
        Create a test user, an initial Client object to modify in the test, and
        some fields to modify it with.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.client_obj = Client.objects.create(hostname='test',
                                            secret_key='secret')
        self.hostname = 'newhostname'
        self.secret_key = 'new_secret_key'

    def test_create_client_view(self):
        """
        Login using the test user, then POST to the update_client view. Check
        that the response code is OK and that the client has been updated
        correctly.
        """
        self.client.login(username='test', password='test')

        response = self.client.post('/clients/%d/update/' %
                                    self.client_obj.id, {
                                        'hostname': self.hostname,
                                        'secret_key': self.secret_key,
                                        'filepaths-TOTAL_FORMS': 0,
                                        'filepaths-INITIAL_FORMS': 0,
                                        'filepaths-MAX_NUM_FORMS': 0,
                                    }, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['object'].hostname, self.hostname)
        self.assertEqual(response.context['object'].secret_key, self.secret_key)
