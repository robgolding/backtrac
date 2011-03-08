"""
Tests for the `clients' application.
"""
from django.test import TestCase
from django.contrib.auth.models import User

from backtrac.apps.clients.models import Client, client_connected, \
        client_disconnected

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

        self.assertIsNotNone(response.context['object'].pk)
        self.assertEqual(response.context['object'].hostname, self.hostname)
        self.assertEqual(response.context['object'].secret_key, self.secret_key)

class InitialStatusTest(TestCase):
    def setUp(self):
        """
        Create a test user and record some test fields for use later on.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.hostname = 'test'
        self.secret_key = 'secret'

    def test_initial_status(self):
        """
        Login using the test user, then POST to the create_client view. Check
        that the client and it's initial status object has been created
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

        self.assertIsNotNone(response.context['object'].status)
        self.assertEqual(response.context['object'],
                         response.context['object'].status.client)

class CreateClientWithFilePathsTest(TestCase):
    def setUp(self):
        """
        Create a test user and record some test fields for use later on.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.hostname = 'test'
        self.secret_key = 'secret'
        self.file_paths = ['/test/one', '/test/two', '/test/three']

    def test_create_client_view(self):
        """
        Login using the test user, then POST to the create_client view. Check
        that the response code is OK and that the client has been created
        correctly, along with the correct file paths for backing up.
        """
        self.client.login(username='test', password='test')

        data = {
            'hostname': self.hostname,
            'secret_key': self.secret_key,
            'filepaths-TOTAL_FORMS': 3,
            'filepaths-INITIAL_FORMS': 0,
            'filepaths-MAX_NUM_FORMS': 3,
        }

        for i, path in enumerate(self.file_paths):
            data['filepaths-%d-path' % i] = path

        response = self.client.post('/clients/create/', data, follow=True)

        self.assertEqual(response.status_code, 200)

        created_paths = [
            p.path for p in response.context['object'].filepaths.all()
        ]

        self.assertEqual(self.file_paths, created_paths)

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

    def test_update_client_view(self):
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

class DeleteClientTest(TestCase):
    def setUp(self):
        """
        Create a test user and an initial Client object to delete in the test.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.client_obj = Client.objects.create(hostname='test',
                                                secret_key='secret')

    def test_delete_client_view(self):
        """
        Login using the test user, then POST to the delete_client view. Check
        that the response code is OK and that the client has been updated
        correctly.
        """
        self.client.login(username='test', password='test')

        response = self.client.post('/clients/%d/delete/' %
                                    self.client_obj.id, {
                                        'confirm': True,
                                    }, follow=True)

        self.assertEqual(response.status_code, 200)

        self.assertRaises(Client.DoesNotExist, Client.objects.get,
                          pk=self.client_obj.id)

class ConnectClientTest(TestCase):
    def setUp(self):
        """
        Create a test Client object to fire the connected signal with.
        """
        self.client_obj = Client.objects.create(hostname='test',
                                                secret_key='secret')

        self.client_obj.status.connected = False

    def test_client_connected_signal(self):
        """
        Test that the client is marked as being connected when the
        client_connected signal is fired.
        """
        client_connected.send(sender=Client, client=self.client_obj)

        self.assertEqual(self.client_obj.status.connected, True)


class DisconnectClientTest(TestCase):
    def setUp(self):
        """
        Create a test Client object to fire the disconnected signal with.
        """
        self.client_obj = Client.objects.create(hostname='test',
                                                secret_key='secret')

        self.client_obj.status.connected = True

    def test_client_disconnected_signal(self):
        """
        Test that the client is marked as being disconnected when the
        client_disconnected signal is fired.
        """
        client_disconnected.send(sender=Client, client=self.client_obj)

        self.assertEqual(self.client_obj.status.connected, False)
