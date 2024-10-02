from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from books.models import Comment, LikeComment, Category, Book, ReadingSession


class ListCommentSerializer(serializers.ListSerializer):
    """
    Filters out comments that are replies.
    Only the root-level comments (where parent=None) are returned.
    """

    def to_representation(self, data):
        data = data.filter(parent=None)
        return super().to_representation(data)


class ReplySerializer(serializers.ModelSerializer):
    """
    Serializer for a reply to a comment, showing the user, body, and number of likes.
    """

    likes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["user", "body", "likes"]

    def get_likes(self, obj):
        return LikeComment.objects.filter(comment=obj).count()


class CommentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed comment representation, including its replies and likes.
    """

    replies = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "user", "book", "body", "parent", "replies", "likes"]

    def get_likes(self, obj):
        return LikeComment.objects.filter(comment=obj).count()

    def get_replies(self, obj):
        if obj.replies.exists():
            queryset = obj.replies.all()
            return ReplySerializer(queryset, many=True).data
        else:
            return None


class CommentsSerializer(serializers.ModelSerializer):
    """
    Serializer for listing comments, with their replies.
    Uses a custom list serializer to filter root-level comments.
    """

    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["user", "book", "body", "replies"]
        list_serializer_class = ListCommentSerializer

    def get_replies(self, obj):
        if obj.replies.exists():
            queryset = obj.replies.all()
            return ReplySerializer(queryset, many=True).data
        else:
            return None


class CreateCommentSerializer(serializers.ModelSerializer):
    """
    Creates a new comment.
    """

    class Meta:
        model = Comment
        fields = ["id", "body", "book", "parent"]
        read_only_fields = ["user"]

    def validate(self, attrs):
        """
        Validates that the parent comment, if provided, belongs to the same book.
        """

        if attrs.get("parent"):
            parent = get_object_or_404(Comment, id=attrs["parent"].id)
            if parent.book != attrs["book"]:
                raise ValidationError(
                    {"detail": "Parent comment must belong to the same book."}
                )
        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        return Comment.objects.create(user=user, **validated_data)


class Category(serializers.ModelSerializer):
    """
    Represents a book category.
    """

    class Meta:
        model = Category
        fields = "__all__"


class BooksSerializer(serializers.ModelSerializer):
    """
    Serializer for listing books, including their categories.
    Categories are represented by their name.
    """

    categories = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "published",
            "categories",
            "short_description",
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed book representation, including last reading session and categories.
    """

    last_reading = serializers.SerializerMethodField()
    categories = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True
    )

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "published",
            "categories",
            "short_description",
            "full_description",
            "text",
            "last_reading",
        ]

    def get_last_reading(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return None
        last_reading = (
            obj.reading_sessions.filter(
                user=self.context.get("request").user, stop_reading__isnull=False
            )
            .order_by("-stop_reading")
            .first()
        )
        if last_reading:
            return last_reading.stop_reading
        else:
            return None


class ReadingSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for representing a reading session.
    """

    class Meta:
        model = ReadingSession
        fields = ["start_reading", "stop_reading"]
        read_only_fields = ["user", "book"]


class StartReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for starting a new reading session.

    Validation:
        - Ensures there is no active reading session for the same book.
        - Automatically sets the start_reading field to the current time.
    """

    class Meta:
        model = ReadingSession
        fields = ["start_reading", "stop_reading"]
        read_only_fields = ["user", "book", "start_reading", "stop_reading"]

    def validate(self, attrs):
        user = self.context.get("request").user
        book = self.context.get("book")

        active_session = ReadingSession.objects.filter(
            user=user, stop_reading__isnull=True
        )
        if active_session.exists():
            if active_session.filter(book=book):
                raise ValidationError(
                    {"detail": "Active reading session already exists"}
                )

            active_session.update(stop_reading=timezone.now())
        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        book = self.context.get("book")
        return ReadingSession.objects.create(
            user=user, book=book, start_reading=timezone.now()
        )


class StopReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for stopping the active reading session.

    Validation:
        - Ensures that the last session is active.
        - Automatically sets the stop field to the current time.
    """

    class Meta:
        model = ReadingSession
        fields = ["start_reading", "stop_reading"]
        read_only_fields = ["user", "book", "start_reading", "stop_reading"]

    def validate(self, attrs):
        if self.instance is None or self.instance.stop_reading is not None:
            raise ValidationError({"detail": "Session is not active"})
        return attrs

    def update(self, instance, validated_data):
        instance.stop_reading = timezone.now()
        instance.save()
        return instance


class LikeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for liking a comment.
    Ensures that a user can only like a comment once.
    """

    class Meta:
        model = LikeComment
        fields = ["user", "comment"]
        read_only_fields = ["user", "comment"]

    def validate(self, attrs):
        user = self.context.get("request").user
        comment = self.context.get("comment")
        like = comment.likes.filter(user=user)
        if like.exists():
            raise ValidationError({"detail": "Like already exists"})
        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        comment = self.context.get("comment")
        return LikeComment.objects.create(user=user, comment=comment)
