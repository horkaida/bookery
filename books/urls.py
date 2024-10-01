from django.urls import path, include
from books.views import CommentViewSet, BookViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register("comments", CommentViewSet, basename="comment")
router.register("books", BookViewSet, basename="book")

urlpatterns = [
    path("", include(router.urls)),
]
