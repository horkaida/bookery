from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers import (CreateUserSerializer, UserActivateSerializer,
                              ResendActivationEmailSerializer,
                              ResetPasswordSerializer, ChangePasswordSerializer, ListUserSerializer, ProfileSerializer)
from user.utils import send_activation_email, send_reset_password_email


User = get_user_model()



class UserSignUpAPIView(CreateAPIView):
    """
    - Allows any user to create a new account.
    - Validates user input and creates a new user instance.
    - Generates and returns refresh and access tokens upon successful signup.
    """

    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({'refresh_token': str(refresh), "access_token": str(refresh.access_token)},
                        status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    API view for user logout.
    - Requires the user to be authenticated.
    - Accepts a refresh token to blacklist it, logging the user out.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        else:
            #TODO refactor
            return Response(status=status.HTTP_200_OK)



class UserViewSet(ModelViewSet):
    """
    ViewSet for managing user-related actions.

    - Handles actions like account activation, resending activation emails, password reset,
      password change, and profile retrieval.
    """

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'head', 'put']

    def get_permissions(self):
        if self.action in ['activate', 'resend_activation', 'request_reset_password', 'reset_password']:
            return [AllowAny()]
        elif self.action in ['change_password', 'profile']:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticatedOrReadOnly()]


    def get_serializer_class(self):
        if self.action=='activate':
            return UserActivateSerializer
        elif self.action=='resend_activation':
            return ResendActivationEmailSerializer
        elif self.action=='reset_password':
            return ResetPasswordSerializer
        elif self.action=='change_password':
            return ChangePasswordSerializer
        elif self.action=='profile':
            return ProfileSerializer
        else:
            return ListUserSerializer


    @action(detail=False, methods=['put'], url_path='activate')
    def activate(self, request, *args, **kwargs):
        """
        Activates the user account upon successful validation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Account activated successfully.'}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='resend_activation')
    def resend_activation(self, request, *args, **kwargs):
        """
        Retrieves the user by email.
        Sends the activation email again.
        """
        email = request.data.get('email')
        user = get_object_or_404(User, email=email)
        serializer = self.get_serializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)

        send_activation_email(user)
        return Response(status=status.HTTP_200_OK)



    @action(detail=False, methods=['post'], url_path='request_reset_password')
    def request_reset_password(self, request, *args, **kwargs):
        """
        Retrieves the user by email.
        Sends the password reset email.
        """
        email = request.data.get('email')
        user = get_object_or_404(User, email=email)

        send_reset_password_email(user)
        return Response(status=status.HTTP_200_OK)


    @action(detail=False, methods=['put'], url_path='reset_password')
    def reset_password(self, request, *args, **kwargs):
        """
        Resets the user's password.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


    @action(detail=False, methods=['put'], url_path='change_password')
    def change_password(self, request, *args, **kwargs):
        """
        Changes the user's password.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_200_OK)


    @action(detail=True, methods=['get'], url_path='profile')
    def profile(self, request, *args, **kwargs):
        """
        Returns the profile information of the current user.
        """
        user = self.get_object()
        serializer = self.get_serializer(user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)








