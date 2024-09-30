from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from rest_framework.validators import UniqueValidator

from user.models import Profile

User = get_user_model()



class ListUserSerializer(serializers.ModelSerializer):
    """
    Serializes the 'username' and 'email' fields of the User model.
    """
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializes the total reading time for the last 7 and 30 days.
    """
    class Meta:
        model = Profile
        fields = ['total_reading_7days', 'total_reading_30days']


class CreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user.
    - Handles user creation, ensuring email uniqueness.
    - Serializes 'username', 'password', and 'email' fields.
    """

    email = serializers.EmailField(required=True, validators=[UniqueValidator(
        queryset=User.objects.all())])
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def validate(self, attrs):
        """
        Validate the provided password against the default password validators.
        """
        password = attrs.get('password')
        validate_password(password)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            is_active=False
        )


class UserActivateSerializer(serializers.Serializer):
    """
    Serializer for activating a user account.
    - Handles the validation of UID and token.
    - Activates the user if the UID and token are valid.
    Fields:
        uidb64 (str): The base64-encoded user ID.
        token (str): The token for account activation.
    """

    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        """
        Validate the UID and token, and activate the user if valid.
        """
        uidb64 = attrs.get('uidb64')
        token = attrs.get('token')
        try:
            # Decode the base64-encoded UID
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            raise serializers.ValidationError({'detail': 'Invalid activation link.'})

        if user.is_active:
            raise serializers.ValidationError({'detail': 'This account is already active.'})

        # Check if the token is valid for the user
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({'detail': 'Invalid or expired token.'})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.is_active = True
        user.save()



class ResendActivationEmailSerializer(serializers.Serializer):
    """
    Serializer for resending the account activation email.
    """
    email = serializers.EmailField()

    def validate(self, attrs):
        """
        Validate the email and ensure the account is not already active.
        """
        user = self.context.get('user')
        if user.is_active:
            raise serializers.ValidationError('This account is already active.')
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting a user's password.
    - Handles password reset using a UID and token.
    - Ensures the new password is valid and not the same as the old password.
    Fields:
        uidb64 (str): The base64-encoded user ID.
        token (str): The token for password reset.
        new_password (str): The new password.
    """

    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        uidb64 = attrs.get('uidb64')
        token = attrs.get('token')
        new_password = attrs.get('new_password')

        validate_password(new_password)
        try:
            # Decode the base64-encoded UID
            uid = force_bytes(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
        except(TypeError, ValueError, User.DoesNotExist):
            raise serializers.ValidationError('Invalid reset link.')

        # Check if the token is valid for the user
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError('Invalid or expired token.')

        if check_password(new_password, user.password):
            raise serializers.ValidationError("New password cannot be the same as the old password.")

        attrs['user']=user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        new_password = self.validated_data.get('new_password')
        user.set_password(new_password)
        user.save()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing a user's password.
    """
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        """
        Ensures the current password is correct.
        Ensures the new password is not the same as the old password.
        """

        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        user = self.context.get('request').user

        if not check_password(current_password, user.password):
            raise serializers.ValidationError({'detail':'Incorrect password'})
        if check_password(new_password, user.password):
            raise serializers.ValidationError({'detail': 'New password cannot be the same as the old password.'})
        validate_password(new_password)

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()









