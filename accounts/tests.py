from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from accounts.models import UserProfile 
import uuid

User = get_user_model()

@override_settings(RATELIMIT_USE_CACHE='default')
class RateLimitTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.verify_otp_url = reverse('verify_otp')
        self.request_reset_url = reverse('request_reset')

        # Create test user & profile
        self.user = User.objects.create(
            email="testuser@example.com",
            username="testuser@example.com",
            password=make_password("TestPassword123!")
        )
        self.profile = UserProfile.objects.create(user=self.user, is_verified=True)

        cache.clear()  # Clear cache to avoid side effects between tests

    def simulate_post_attempts(self, url, data, times):
        for i in range(times):
            response = self.client.post(url, data)
        return response

    def test_signup_rate_limit(self):
        data = {
            'email': 'newuser@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        }
        response = self.simulate_post_attempts(self.signup_url, data, 6)
        self.assertContains(response, "Too many", status_code=200)

    def test_login_rate_limit(self):
        data = {
            'username': 'testuser@example.com',  # Note: Django uses 'username' not 'email' here
            'password': 'TestPassword123!'
        }
        response = self.simulate_post_attempts(self.login_url, data, 6)
        self.assertContains(response, "Too many", status_code=200)

    def test_verify_otp_rate_limit(self):
        # Set OTP session manually to simulate prior login step
        self.client.session['user_id_for_otp'] = self.user.id
        self.client.session.save()

        # Save correct OTP to profile for validity test
        otp = self.profile.generate_otp()
        data = {'otp': '999999'}  # Use wrong OTP intentionally

        response = self.simulate_post_attempts(self.verify_otp_url, data, 6)
        self.assertContains(response, "Too many", status_code=200)

    def test_request_password_reset_rate_limit(self):
        data = {'email': 'testuser@example.com'}
        response = self.simulate_post_attempts(self.request_reset_url, data, 6)
        self.assertContains(response, "Too many", status_code=200)

    def test_reset_password_rate_limit(self):
        token = self.profile.generate_reset_token()
        reset_url = reverse('reset_password', kwargs={'token': token})
        data = {
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        }

        response = self.simulate_post_attempts(reset_url, data, 6)
        self.assertContains(response, "Too many", status_code=200)
