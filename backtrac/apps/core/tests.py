"""
Tests for the `core' application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from backtrac.apps.core.models import GlobalExclusion

class GlobalExclusionsTest(TestCase):
    def setUp(self):
        """
        Create a test user with which to perform the main test.
        """
        User.objects.create_user('test', 'test@test.com', 'test')

        self.exclusions = [
            '*.txt',
            '.*.swp',
            '*.tmp',
        ]

    def test_configure_global_exclusions(self):
        """
        Test that the global exclusions are correctly added to the database
        when they are configured through the web interface.
        """
        self.client.login(username='test', password='test')

        data = {
            'exclusions-TOTAL_FORMS': 3,
            'exclusions-INITIAL_FORMS': 0,
            'exclusions-MAX_NUM_FORMS': 3,
        }

        for i, glob in enumerate(self.exclusions):
            data['exclusions-%d-glob' % i] = glob

        response = self.client.post(reverse('core_config'), data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [ e.glob for e in GlobalExclusion.objects.all() ],
            self.exclusions
        )
