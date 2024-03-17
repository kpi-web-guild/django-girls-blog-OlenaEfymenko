"""Tests for the views functions."""
from datetime import datetime
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post


class ViewsTest(TestCase):
    """Tests for views in Blog application."""

    @classmethod
    def setUpTestData(cls):
        """Create test client, user, posts with different published dates."""
        cls.user = get_user_model().objects.create()
        cls.client = Client()
        cls.tm_zone = timezone.get_current_timezone()

        cls.past_post = Post.objects.create(
            author=cls.user,
            title='test past post',
            published_date=datetime(2016, 1, 4, tzinfo=cls.tm_zone),
        )

        cls.current_post = Post.objects.create(
            author=cls.user,
            title='test current post',
            published_date=datetime(2024, 3, 1, tzinfo=cls.tm_zone),
        )

        cls.future_post = Post.objects.create(
            author=cls.user,
            title='test future post',
            published_date=datetime(2030, 3, 1, tzinfo=cls.tm_zone),
        )

    def test_post_list_rendering(self):
        """Check correct posts displayed based on mocked current time."""
        post_list_url = reverse('post_list')
        posts_seen_at_different_times = {
            # before the oldest post
            datetime(2015, 1, 2, tzinfo=self.tm_zone):
                [],
            # after the oldest post
            datetime(2024, 2, 1, tzinfo=self.tm_zone):
                [self.past_post],
            # right after the current post, before the future one
            datetime(2024, 3, 2, tzinfo=self.tm_zone):
                [self.past_post, self.current_post],
            # in the distant future, when all the posts are published
            datetime(2030, 4, 1, tzinfo=self.tm_zone):
                [self.past_post, self.current_post, self.future_post],
        }
        for now, expected_posts in posts_seen_at_different_times.items():
            with self.subTest(msg=f'Mocking current date as {now!s}'):
                with patch(
                    'django.utils.timezone.now',
                    Mock(return_value=now),
                ):
                    http_response = self.client.get(post_list_url)
                self.assertListEqual(
                    list(http_response.context['posts']),
                    expected_posts,
                )
                self.assertEqual(200, http_response.status_code)
                self.assertTemplateUsed(http_response, 'blog/post_list.html')

    def test_post_detail_successful(self):
        """Ensure an existing post is found by ID."""
        post = Post.objects.create(
            author=self.user, title='test title', text='test text',
        )
        http_response = self.client.get(
            reverse('post_detail', kwargs={'pk': post.pk}),
        )
        self.assertEqual(200, http_response.status_code)
        self.assertTemplateUsed(http_response, 'blog/post_detail.html')

    def test_post_detail_failed(self):
        """Check that getting a non-existent post returns 404."""
        http_response = self.client.get(
            reverse('post_detail', kwargs={'pk': 31}),
        )
        self.assertEqual(404, http_response.status_code)
