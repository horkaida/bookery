from django.urls import path
from rest_framework.routers import DefaultRouter

from user.views import LogoutView, UserSignUpAPIView, UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register("user", UserViewSet, basename="user")

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/signup/", UserSignUpAPIView.as_view(), name="signup"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urlpatterns += router.urls
