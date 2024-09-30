from rest_framework_simplejwt.tokens import RefreshToken


def get_jwt_for_user(user):
    """
    Generates a JWT token for the provided user.
    """
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def get_auth_headers(access_token):
    """Helper method to include the JWT token in the Authorization header."""
    return {
        'HTTP_AUTHORIZATION': f'Bearer {access_token}'
    }

