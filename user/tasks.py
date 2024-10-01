from datetime import timedelta
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.utils import timezone

from books.models import ReadingSession
from user.models import Profile

User = get_user_model()


@shared_task
def reading_time_statistic():
    """
    Computes the total reading time for each user's reading sessions
    over the last 7 days and the last 30 days. Then updates the corresponding
    fields in the user's profile with the calculated durations in seconds.
    """
    # Calculate the cutoff timestamps for 7 and 30 days ago
    seven_days_ago = timezone.now() - timedelta(days=7)
    thirty_days_ago = timezone.now() - timedelta(days=30)

    profiles = Profile.objects.all()

    for profile in profiles:
        # Calculate total reading time for the last 7 days
        total_reading_7days = ReadingSession.objects.filter(
            user=profile.user, stop_reading__gte=seven_days_ago
        ).aggregate(duration=Sum(F("stop_reading") - F("start_reading")))["duration"]
        # Convert the total reading time to seconds, default to 0 if None
        total_reading_7days_seconds = (
            total_reading_7days.total_seconds() if total_reading_7days else 0
        )

        # Calculate total reading time for the last 30 days
        total_reading_30days = ReadingSession.objects.filter(
            user=profile.user, stop_reading__gte=thirty_days_ago
        ).aggregate(duration=Sum(F("stop_reading") - F("start_reading")))["duration"]
        # Convert the total reading time to seconds, default to 0 if None
        total_reading_30days_seconds = (
            total_reading_30days.total_seconds() if total_reading_30days else 0
        )

        Profile.objects.filter(id=profile.id).update(
            total_reading_7days=int(total_reading_7days_seconds),
            total_reading_30days=int(total_reading_30days_seconds),
        )
