"""
Automated tests for the accounts app: registration and login.

Run with:  python manage.py test
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile

User = get_user_model()


class UserRegistrationTests(TestCase):
    """Test 1: user registration."""

    def test_registration_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'SuperSecret123!',
            'password2': 'SuperSecret123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Registering should also log the user in immediately.
        self.assertIn('_auth_user_id', self.client.session)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(username='existing', email='taken@example.com', password='pass12345')
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newperson',
            'email': 'taken@example.com',
            'password1': 'SuperSecret123!',
            'password2': 'SuperSecret123!',
        })
        self.assertEqual(response.status_code, 200)  # re-renders form with errors
        self.assertFalse(User.objects.filter(username='newperson').exists())

    def test_profile_is_auto_created_for_new_user(self):
        user = User.objects.create_user(username='autop', password='pass12345')
        self.assertTrue(Profile.objects.filter(user=user).exists())


class LoginTests(TestCase):
    """Test 2: login (including the "login with email" behavior)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', email='login@example.com', password='CorrectPass123',
        )

    def test_login_with_username_succeeds(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'CorrectPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:home'))

    def test_login_with_email_succeeds(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'login@example.com',
            'password': 'CorrectPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_with_wrong_password_fails(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)
