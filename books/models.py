from django.db import models
from django.conf import settings


class Category(models.Model):
    """
    Model representing a book category.
    """

    name = models.CharField(100)

    def __str__(self):
        return self.name


class Book(models.Model):
    """
    Model representing a book.
    """

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    text = models.TextField()
    published = models.CharField(100)
    short_description = models.TextField(max_length=250)
    full_description = models.TextField(max_length=1000)
    categories = models.ManyToManyField(Category, related_name="books")

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )

    def __str__(self):
        return f"Comment by {self.user} on {self.book.title}"


class LikeComment(models.Model):
    """
    Model representing a like on a comment.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")

    def __str__(self):
        return f"{self.user} liked a comment on {self.comment.book.title}"


class ReadingSession(models.Model):
    """
    Model representing a reading session for a user.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="reading_sessions"
    )
    start_reading = models.DateTimeField(blank=True, null=True)
    stop_reading = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} reading {self.book.title} from {self.start_reading} to {self.stop_reading}"
