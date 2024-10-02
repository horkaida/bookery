from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def generate_token(user):
    # Generate a time-limited token that is linked to the user's account
    token = default_token_generator.make_token(user)
    # Encode the user's primary key into a base64 string to safely include in the URL
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return uidb64, token


def send_activation_email(user):
    """
    Sends an account activation email to a user with a unique activation link.
    """
    uidb64, token = generate_token(user)
    activation_link = f"{settings.FRONTEND_URL}/activate?uidb64={uidb64}&token={token}"
    subject = "Activate Your Account"
    message = f"Hi {user.username},\n\nPlease activate your account by clicking the link below:\n{activation_link}"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])


def send_reset_password_email(user):
    """
    Sends a password reset email to the user with a unique reset link.
    """
    uidb64, token = generate_token(user)
    reset_password_link = (
        f"{settings.FRONTEND_URL}/activate?uidb64={uidb64}&token={token}"
    )
    subject = "Password Reset"
    message = f"Hi {user.username},\n\nPlease reset your password by clicking the link below:\n{reset_password_link}"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
