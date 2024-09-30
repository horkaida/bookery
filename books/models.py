from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(100)


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    text = models.TextField()
    published = models.CharField(100)
    short_description = models.TextField(max_length=250)
    full_description = models.TextField(max_length=1000)
    categories = models.ManyToManyField(Category, related_name='books')


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')


class LikeComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')


class ReadingSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reading_sessions')
    start_reading = models.DateTimeField(blank=True, null=True)
    stop_reading = models.DateTimeField(blank=True, null=True)
