"""Tests for the Post model."""

from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from blog.models import Post

User = get_user_model()


class TestPostModel(TestCase):
    """Tests for the Post model."""

    def setUp(self):
        """Create test User and Post objects."""
        self.user = User.objects.create(username='test user')
        self.test_post = Post.objects.create(
            author=self.user,
            title='test title',
            text='test text',
        )

    @patch(
        'django.utils.timezone.now', lambda: datetime(
            day=12,
            month=1,
            year=2024,
            tzinfo=timezone.get_current_timezone(),
        ),
    )
    def test_post_publish(self):
        """Ensure publishing a post sets its date."""
        self.assertIsNone(self.test_post.published_date)
        self.test_post.publish()
        self.assertEqual(
            self.test_post.published_date, datetime(
                day=12,
                month=1,
                year=2024,
                tzinfo=timezone.get_current_timezone(),
            ),
        )

    def test_post_str(self):
        """Check that the Post's string representation uses its title."""
        self.assertEqual(str(self.test_post), self.test_post.title)

    def tearDown(self):
        """Clean test data."""
        del self.user
        del self.test_post
