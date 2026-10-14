from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser


class SignUpViewTests(TestCase):
    def test_signup_creates_user_and_logs_user_in(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'newuser',
                'first_name': 'New',
                'last_name': 'User',
                'email': 'newuser@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class EmailOrUsernameLoginTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='salonclient',
            email='client@example.com',
            password='StrongPass123!',
        )

    def test_login_accepts_username(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'salonclient', 'password': 'StrongPass123!'},
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_accepts_email_case_insensitively(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'CLIENT@EXAMPLE.COM', 'password': 'StrongPass123!'},
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_rejects_unknown_email(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'unknown@example.com', 'password': 'StrongPass123!'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

# Create your tests here.
