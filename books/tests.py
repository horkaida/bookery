from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from books.models import *
from django.utils import timezone

from utils.test_utils import get_jwt_for_user, get_auth_headers

User = get_user_model()



class BookAndCommentTest(APITestCase):
    # TODO RESOLVE ISSUE REGARDING FIXTURE
    fixtures = ["fixture.json"]

    def setUp(self):
        """Set up the test case by creating a user and getting authentication headers."""
        self.user = User.objects.first()
        self.auth_headers = get_auth_headers(get_jwt_for_user(self.user))


    def test_book_list_unauthorized(self):
        """Test retrieving the book list without authentication."""
        url = reverse('book-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data)
        expected_fields = ['id', 'title', 'author', 'published', 'categories', 'short_description',]

        # Check that all expected fields are present no additional fields are included
        for book in response.data:
            self.assertSetEqual(set(book.keys()), set(expected_fields))


    def test_book_list_authorized(self):
        """Test retrieving the book list with authentication."""
        url = reverse('book-list')
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data)
        expected_fields = ['id', 'title', 'author', 'published', 'categories', 'short_description']

        # Check that all expected fields are present no additional fields are included
        for book in response.data:
            self.assertSetEqual(set(book.keys()), set(expected_fields))


    def test_book_detail_unauthorized(self):
        """Test retrieving book details without authentication."""
        url = reverse('book-detail', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = [
            'id', 'title', 'author', 'published', 'categories', 'short_description', 'full_description', 'text',
            'last_reading'
        ]
        #Checks that last_reading field is None for unauthorized user
        self.assertIsNone(response.data['last_reading'])

        # Check that all expected fields are present no additional fields are included
        self.assertSetEqual(set(response.data.keys()), set(expected_fields))



    def test_book_detail_authorized(self):
        """Test retrieving book details with authentication."""
        url = reverse('book-detail', kwargs={'pk':1})
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = [
            'id', 'title', 'author', 'published', 'categories', 'short_description', 'full_description', 'text',
            'last_reading'
        ]
        # Check that all expected fields are present no additional fields are included
        self.assertSetEqual(set(response.data.keys()), set(expected_fields))


    def test_book_statistic_unauthorized(self):
        """Test retrieving book statistics without authentication."""
        url = reverse('book-statistic', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_book_statistic_authorized(self):
        """Test retrieving book statistics with authentication."""
        url = reverse('book-statistic', kwargs={'pk':1})
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reading_seconds', response.data)


    def test_start_reading_unauthorized(self):
        """Test starting a reading session without authentication."""
        url = reverse('book-start-reading', kwargs={'pk':1})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_start_reading_authorized(self):
        """Test starting a reading session with authentication."""
        url = reverse('book-start-reading', kwargs={'pk':1})
        response = self.client.post(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('start_reading', response.data)
        self.assertIsNone(response.data['stop_reading'])


    def test_start_reading_with_active_previous_session(self):
        """Test starting a reading session when a previous session is active."""
        previous_reading_session = ReadingSession.objects.create(
            book_id=2, start_reading=timezone.now(), stop_reading=None, user_id=self.user.id
        )
        url = reverse('book-start-reading', kwargs={'pk': 1})
        response = self.client.post(url, **self.auth_headers)
        previous_reading_session.refresh_from_db()

        # Assert that the response is successful and the previous session is updated correctly.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['start_reading'])
        self.assertIsNone(response.data['stop_reading'])
        self.assertIsNotNone(previous_reading_session.stop_reading)


    def test_same_active_reading_session_already_exists(self):
        """Test starting a reading session when an active session already exists."""
        ReadingSession.objects.create(
            book_id=1, start_reading=timezone.now(), stop_reading=None, user_id=self.user.id
        )

        url = reverse('book-start-reading', kwargs={'pk': 1})
        response = self.client.post(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Active reading session already exists', response.data['detail'])



    def test_start_reading_invalid_book_id(self):
        """Test starting a reading session with an invalid book ID."""
        url = reverse('book-start-reading', kwargs={'pk': 111111})
        response = self.client.post(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_stop_reading_authorized(self):
        """Test stopping a reading session with authentication."""
        last_reading_session = ReadingSession.objects.create(
            book_id=1, start_reading=timezone.now(), stop_reading=None, user_id=self.user.id
        )
        url = reverse('book-stop-reading', kwargs={'pk':1})
        response = self.client.put(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['stop_reading'])

        # Get the last reading session for the user and ensure it matches the last session created.
        last_session = ReadingSession.objects.filter(user=self.user).last()
        self.assertEqual(last_reading_session.id, last_session.id)


    def test_stop_reading_unauthorized(self):
        """Test stopping a reading session without authentication."""
        url = reverse('book-stop-reading', kwargs={'pk': 1})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_stop_reading_session_not_active(self):
        """Test stopping a reading session that is not active."""
        url = reverse('book-stop-reading', kwargs={'pk': 1})
        response = self.client.put(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Session is not active', response.data['detail'])


    def test_stop_reading_invalid_book_id(self):
        """Test stopping reading with an invalid book ID returns 404 Not Found."""
        url = reverse('book-stop-reading', kwargs={'pk': 1111111})
        response = self.client.put(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


############

    def test_comments_list_unauthorized(self):
        """Test that the comments list is accessible without authentication
        and that the response contains the expected fields."""
        url = reverse('comment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = ['user', 'book', 'body', 'replies']

        # Check that all expected fields are present no additional fields are included
        for comment in response.data:
            self.assertSetEqual(set(comment.keys()), set(expected_fields))


    def test_comments_list_authorized(self):
        """Test that the comments list is accessible with authentication
        and that the response contains the expected fields."""
        url = reverse('comment-list')
        response = self.client.get(url, self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = ['user', 'book', 'body', 'replies']

        # Check that all expected fields are present no additional fields are included
        for comment in response.data:
            self.assertSetEqual(set(comment.keys()), set(expected_fields))


    def test_create_comment_unauthorized(self):
        """Test that creating a comment without authentication returns 401 Unauthorized."""
        url = reverse('comment-list')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_comment_authorized(self):
        """Test that an authenticated user can create a comment successfully."""
        url = reverse('comment-list')
        response = self.client.post(url, data={'body': 'commenttest', 'book': 1}, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_create_comment_empty_body(self):
        """Test that creating a comment with an empty body returns 400 Bad Request
        with an appropriate error message."""
        url = reverse('comment-list')
        response = self.client.post(url, data={'body': '', 'book': 1}, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('This field may not be blank.', response.data['body'])


    def test_create_comment_invalid_book(self):
        """Test that creating a comment with an invalid book ID returns 400 Bad Request."""
        url = reverse('comment-list')
        response = self.client.post(url, data={'body': 'commnettest', 'book': 11111111111}, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_create_reply_authorized(self):
        """Test that an authenticated user can create a reply to an existing comment successfully."""
        url = reverse('comment-list')
        existing_comment = Comment.objects.first()
        response = self.client.post(
            url,
            data={'body': 'replytest', 'book': existing_comment.book.id, 'parent': existing_comment.id},
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_create_reply_invalid_book(self):
        """Test that creating a reply to a comment with a different book ID returns
        400 Bad Request with an appropriate error message."""
        url = reverse('comment-list')
        existing_comment = Comment.objects.first()
        response = self.client.post(
            url,
            data={'body': 'replytest', 'book': 2, 'parent': existing_comment.id},
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Parent comment must belong to the same book.', response.data['detail'])


    def test_delete_comment_unauthorized(self):
        """Test that deleting a comment without authentication returns 401 Unauthorized."""
        comment = Comment.objects.first()
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_delete_comment_authorized_owner(self):
        """Test that an authenticated user can delete their own comment successfully."""
        comment = Comment.objects.filter(user=self.user).first()
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        response = self.client.delete(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


    def test_delete_comment_authorized_not_owner(self):
        """Test that an authenticated user cannot delete a comment that they do not own,
            returning 403 Forbidden."""
        another_user = User.objects.get(id=2)
        comment = Comment.objects.filter(user=another_user).first()
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        response = self.client.delete(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_update_comment_unauthorized(self):
        """Test that updating a comment without authentication returns 401 Unauthorized."""
        comment = Comment.objects.first()
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        response = self.client.put(
            url,
            data={'body': 'testcomment', 'book': comment.book.id, 'parent': comment.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_update_comment_authorized_not_owner(self):
        """Test that an authenticated user cannot update a comment that they do not own,
        returning 403 Forbidden."""
        another_user = User.objects.get(id=2)
        comment = Comment.objects.filter(user=another_user).first()
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        response = self.client.put(
            url,
            data={'body': 'testcomment', 'book': comment.book.id, 'parent': comment.id},
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_upvote_comment_unauthorized(self):
        """Test that upvoting a comment without authentication returns 401 Unauthorized."""
        comment = Comment.objects.filter(likes__isnull=True).first()
        url = reverse('comment-upvote', kwargs={'pk': comment.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_upvote_comment_authorized(self):
        """Test that an authenticated user can upvote a comment successfully."""
        comment = Comment.objects.filter(likes__isnull=True).first()
        url = reverse('comment-upvote', kwargs={'pk': comment.id})
        response = self.client.post(url, **self.auth_headers)
        like = comment.likes.filter(user=self.user, comment=comment)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(like)


    def test_upvote_comment_like_from_this_user_already_exists(self):
        """Test that upvoting a comment that the user has already liked returns
        400 Bad Request with an appropriate error message."""
        comment = Comment.objects.filter(likes__isnull=True).first()
        LikeComment.objects.create(user=self.user, comment=comment)
        url = reverse('comment-upvote', kwargs={'pk': comment.id})
        response = self.client.post(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Like already exists', response.data['detail'])


    def test_downvote_comment_unauthorized(self):
        """Test that downvoting a comment without authentication returns 401 Unauthorized."""
        comment = Comment.objects.filter(likes__isnull=True).first()
        LikeComment.objects.create(user=self.user, comment=comment)
        url = reverse('comment-downvote', kwargs={'pk': comment.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_downvote_comment_authorized(self):
        """Test that an authenticated user can downvote a comment successfully."""
        comment = Comment.objects.filter(likes__isnull=True).first()
        LikeComment.objects.create(user=self.user, comment=comment)
        url = reverse('comment-downvote', kwargs={'pk': comment.id})
        response = self.client.delete(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


    def test_downvote_comment_authorized_like_not_exist(self):
        """Test that downvoting a comment that the user has not liked returns
        404 Not Found with an appropriate error message."""
        comment = Comment.objects.filter(likes__isnull=True).first()
        url = reverse('comment-downvote', kwargs={'pk': comment.id})
        response = self.client.delete(url, **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Like does not exist', response.data['detail'])


