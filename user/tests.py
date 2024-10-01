from datetime import timedelta
from unittest import TestCase
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import ReadingSession, Book
from user.models import Profile
from user.tasks import reading_time_statistic
from utils.test_utils import get_jwt_for_user, get_auth_headers

User = get_user_model()


class UserSignUpTest(APITestCase):
    """Tests for user signup and associated functionality."""

    @patch("user.signals.send_activation_email")
    def test_user_registration_sends_activation_email(self, mock_send_mail):
        """
        Test that a successful user registration sends an activation email.
        Mocks the `send_activation_email` function and verifies that it is called after registration.
        """
        url = reverse("signup")
        data = {
            "username": "testuser",
            "password": "strongpassword123",
            "email": "test@gmail.com",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        user = User.objects.get(username="testuser")
        self.assertIsNotNone(user)

        # Checks if the email was sent
        mock_send_mail.assert_called_once_with(user)

    def test_is_profile_created(self):
        """
        Test that a user profile is created when a user signs up.
        Ensures that a profile is automatically associated with the user.
        """
        url = reverse("signup")
        data = {
            "username": "testuser",
            "password": "strongpassword123",
            "email": "test@gmail.com",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="testuser")
        self.assertIsNotNone(user)
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile)


class UserSignUpTestInvalidEmail(APITestCase):
    """Tests for invalid email cases during user registration."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="strongpassword123", email="test@gmail.com"
        )

    @patch("user.signals.send_activation_email")
    def test_registration_email_already_exists(self, mock_send_mail):
        """
        Test registration with an already existing email.
        Verifies that the registration fails and no activation email is sent.
        """
        url = reverse("signup")
        data = {
            "username": "test1user",
            "password": "strongpassword123",
            "email": "test@gmail.com",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field must be unique.", response.data["email"])
        # Checks if the email was not sent
        mock_send_mail.assert_not_called()

    @patch("user.signals.send_activation_email")
    def test_registration_invalid_email(self, mock_send_mail):
        url = reverse("signup")
        data = {
            "username": "test1user",
            "password": "strongpassword123",
            "email": "email",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid email address.", response.data["email"])
        # Checks if the email was not sent
        mock_send_mail.assert_not_called()


class UserActivationTest(APITestCase):
    """Tests for user account activation functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="strongpassword123",
            email="test@gmail.com",
            is_active=False,
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_account_activation(self):
        """
        Test account activation using a valid token.
        Verifies that the user is activated and receives a 200 OK response.
        """
        url = reverse("user-activate")
        response = self.client.put(
            url, data={"uidb64": self.uidb64, "token": self.token}
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_active)

    def test_account_activation_invalid_token(self):
        """
        Test account activation with an invalid token.
        Verifies that the activation fails with a 400 BAD REQUEST response.
        """
        url = reverse("user-activate")
        response = self.client.put(
            url, data={"uidb64": self.uidb64, "token": "invalidtoken"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired token.", response.data["detail"])
        uid = force_bytes(urlsafe_base64_decode(self.uidb64))
        user = User.objects.get(id=uid)
        self.assertFalse(user.is_active)

    @patch("user.views.send_activation_email")
    def test_resend_activation(self, mock_send_mail):
        """
        Test resending the activation email.
        Mocks the `send_activation_email` function and verifies it is called when requested.
        """
        url = reverse("user-resend-activation")
        response = self.client.post(url, data={"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_mail.assert_called_once_with(self.user)

    @patch("user.views.send_activation_email")
    def test_resend_activation_invalid_email(self, mock_send_mail):
        """
        Test resending activation email with an invalid email address.
        Verifies that the request fails and no email is sent.
        """
        url = reverse("user-resend-activation")
        response = self.client.post(url, data={"email": "invalid_email"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_send_mail.assert_not_called()


class ChangeAndResetPasswordTest(APITestCase):
    """Tests for changing and resetting passwords."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="strongpassword123", email="test@gmail.com"
        )
        """Set up authentication headers for password tests."""
        self.auth_headers = get_auth_headers(get_jwt_for_user(self.user))

    def test_change_password(self):
        """
        Test changing the user's password with a correct current password.
        Verifies that the password is changed successfully.
        """
        url = reverse("user-change-password")
        response = self.client.put(
            url,
            data={
                "current_password": "strongpassword123",
                "new_password": "newpasswordtest",
            },
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(check_password("newpasswordtest", self.user.password))

    def test_change_password_current_password_is_incorrect(self):
        """
        Test changing the password with an incorrect current password.
        Verifies that the request fails with a 400 BAD REQUEST response.
        """
        url = reverse("user-change-password")
        response = self.client.put(
            url,
            data={
                "current_password": "incorectpass",
                "new_password": "newpasswordtest",
            },
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Incorrect password", response.data["detail"])

    def test_change_password_same_as_old(self):
        """
        Test changing the password to the same as the old password.
        Verifies that the request fails with a 400 BAD REQUEST response.
        """
        url = reverse("user-change-password")
        response = self.client.put(
            url,
            data={
                "current_password": "strongpassword123",
                "new_password": "strongpassword123",
            },
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "New password cannot be the same as the old password.",
            response.data["detail"],
        )

    @patch("user.views.send_reset_password_email")
    def test_request_reset_password(self, mock_send_mail):
        """
        Test requesting a password reset for an existing user.
        Verifies that a reset email is sent.
        """
        url = reverse("user-request-reset-password")
        response = self.client.post(url, data={"email": "test@gmail.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email="test@gmail.com")
        self.assertIsNotNone(user)
        mock_send_mail.assert_called_once_with(user)

    @patch("user.views.send_reset_password_email")
    def test_request_reset_password_invalid_email(self, mock_send_mail):
        """
        Test requesting a password reset for a non-existent user.
        Verifies that the request fails and no email is sent.
        """
        url = reverse("user-request-reset-password")
        response = self.client.post(url, data={"email": "invalid@gmail.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Assert that the email sending function was not called
        mock_send_mail.assert_not_called()

    def test_reset_password(self):
        """
        Test resetting the user's password using a valid token and uidb64.
        Verifies that the password is reset successfully.
        """
        url = reverse("user-reset-password")
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.put(
            url,
            data={
                "uidb64": uidb64,
                "token": token,
                "new_password": "strongnewpassword",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(check_password("strongnewpassword", self.user.password))


class ProfileTest(APITestCase):
    """
    Test  fetching profile details for a user.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="strongpassword123", email="test@gmail.com"
        )
        self.auth_headers = get_auth_headers(get_jwt_for_user(self.user))
        self.user.profile.total_reading_7days = 600
        self.user.profile.total_reading_30days = 1000
        self.user.profile.save()

    def test_profile_list_authorized(self):
        """
        Test if an authorized user can retrieve their profile information, and check
        that the reading statistics are correctly returned.
        """
        url = reverse("user-profile", kwargs={"pk": self.user.id})
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_reading_7days"], 600)
        self.assertEqual(response.data["total_reading_30days"], 1000)

    def test_profile_list_unauthorized(self):
        url = reverse("user-profile", kwargs={"pk": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReadingStatisticTest(TestCase):

    def setUp(self):
        """
        Set up a test user and book. Create multiple reading sessions to simulate
        reading over different time periods (within 7 days, 30 days, and older than 30 days).
        """
        self.user = User.objects.create_user(
            username="testuser", password="strongpassword123", email="test@gmail.com"
        )
        self.auth_headers = get_auth_headers(get_jwt_for_user(self.user))
        self.book = Book.objects.create(
            title="title",
            author="author",
            text="text",
            published="2000",
            short_description="short",
            full_description="full",
        )
        # Create reading sessions within and outside the 7 and 30 day windows
        now = timezone.now()
        self.reading_session_1 = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            start_reading=now - timedelta(days=5, hours=1),
            stop_reading=now - timedelta(days=5),
        )
        self.reading_session_2 = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            start_reading=now - timedelta(days=15, hours=2),
            stop_reading=now - timedelta(days=15),
        )
        self.reading_session_3 = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            start_reading=now - timedelta(days=35, hours=3),
            stop_reading=now - timedelta(days=35),
        )

    def test_reading_time_statistic_authorized(self):
        """
        Test the calculation and updating of reading time statistics in the user's profile.
        Ensure that reading time over the last 7 days and 30 days is correctly computed
        based on reading sessions.
        """
        reading_time_statistic()
        self.user.profile.refresh_from_db()

        # Check if the profile has updated reading statistics
        self.assertEqual(
            self.user.profile.total_reading_7days, 3600
        )  # 1 hour = 3600 seconds
        self.assertEqual(
            self.user.profile.total_reading_30days, 10800
        )  # 3 hours in total
