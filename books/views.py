from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.db.models import Sum, F
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from books.models import Book, ReadingSession, Comment
from books.permissions import IsOwnerOrReadOnly
from books.serializers import (
    BooksSerializer,
    BookDetailSerializer,
    CommentDetailSerializer, StartReadingSerializer, StopReadingSerializer, LikeCreateSerializer,
    CommentsSerializer, CreateCommentSerializer
)


class BookViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for retrieving books.
    Includes custom actions for starting/stopping reading sessions and
    retrieving statistics related to reading time.
    """
    queryset = Book.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BooksSerializer
        elif self.action == 'retrieve':
            return BookDetailSerializer
        elif self.action == 'start_reading':
            return StartReadingSerializer
        elif self.action == 'stop_reading':
            return StopReadingSerializer

    def get_permissions(self):
        if self.action in ['statistic', 'start_reading', 'stop_reading']:
            return [IsAuthenticated()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticatedOrReadOnly()]
        else:
            return [IsAuthenticatedOrReadOnly()]

    @action(detail=True, methods=['get'])
    def statistic(self, request, *args, **kwargs):
        """
        Retrieves the total reading time (in seconds) for the specified book.
        The total time is calculated based on the user's reading sessions.
        """

        book = self.get_object()
        total_reading_time = ReadingSession.objects.filter(
            user=request.user, book=book).aggregate(
            duration=Sum(F('stop_reading') - F('start_reading')))['duration']

        total_reading_seconds = total_reading_time.total_seconds() if total_reading_time else 0
        return Response({"total_reading_seconds": int(total_reading_seconds)})

    @action(detail=True, methods=['post'])
    def start_reading(self, request, *args, **kwargs):
        """
        Starts a new reading session for the specified book.
        If an active session for the same book exists, it raises a ValidationError.
        If another session is active, it ends it automatically.
        """

        book = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'request': request, 'book': book})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def stop_reading(self, request, *args, **kwargs):
        """
        Ends the existing session for the specified book.
        If the last reading session for the specified book is not active,
        returns ValidationError.

        """
        book = self.get_object()
        last_session = ReadingSession.objects.filter(
            user=request.user, book=book).last()
        serializer = self.get_serializer(data=request.data, instance=last_session)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(ModelViewSet):
    """
    ViewSet for managing comments on books.
    Includes filters, permissions, and custom actions for upvoting/downvoting comments.
    """

    queryset = Comment.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['book_id']
    http_method_names = ['get', 'post', 'head', 'put', 'delete']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CommentDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CreateCommentSerializer
        elif self.action == 'upvote':
            return LikeCreateSerializer
        elif self.action == 'list':
            return CommentsSerializer

    def get_permissions(self):
        if self.action in ['update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        elif self.action == 'upvote':
            return [IsAuthenticated()]
        else:
            return [IsAuthenticatedOrReadOnly()]

    @action(detail=True, methods=['post'])
    def upvote(self, request, *args, **kwargs):
        """
        Upvotes a comment by the current user.
        """
        comment = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'request': request, 'comment': comment})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def downvote(self, request, *args, **kwargs):
        """
        Removes a user's upvote from a comment if it exists.
        If the upvote does not exist, raises a NotFound error.
        """
        comment = self.get_object()
        like = comment.likes.filter(user=request.user).first()
        if like:
            like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise NotFound({'detail': 'Like does not exist'})


