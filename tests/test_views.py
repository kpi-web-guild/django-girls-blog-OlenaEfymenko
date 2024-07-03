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

        cls.valid_form_post = {
            'title': 'Test Title',
            'text': 'Test Text',
        }

        cls.invalid_form_post = {
            'title': '',
            'text': 'Test Text',
        }

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

    def test_post_new_get_authorized(self):
        """Ensure authorized users can access the new post page."""
        self.client.force_login(self.user)
        url = reverse('post_new')
        http_response = self.client.get(url)
        self.assertEqual(http_response.status_code, 200)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')

    def test_post_new_get_unauthorized(self):
        """Ensure unauthorized users are redirected when add the new post."""
        self.client.logout()
        url = reverse('post_new')
        http_response = self.client.get(url)
        self.assertRedirects(http_response, f'/accounts/login/?next={url}')

    def test_post_new_valid_form_authorized(self):
        """Ensure authorized users can correctly fill out the form for post."""
        self.client.force_login(self.user)
        url = reverse('post_new')
        initial_post_count = Post.objects.count()
        http_response = self.client.post(
            url, self.valid_form_post, follow=True,
        )
        self.assertEqual(http_response.status_code, 200)
        self.assertTemplateUsed(http_response, 'blog/post_detail.html')
        new_post = Post.objects.last()
        self.assertRedirects(
            http_response,
            reverse(
                'post_detail',
                kwargs={'pk': new_post.pk},
            ),
        )
        self.assertEqual(new_post.title, 'Test Title')
        self.assertEqual(new_post.text, 'Test Text')
        self.assertEqual(new_post.author, self.user)
        self.assertIsNotNone(new_post.published_date)
        self.assertEqual(Post.objects.count(), initial_post_count + 1)

    def test_post_new_invalid_form_authorized(self):
        """Test handling of invalid form submission for new post."""
        self.client.force_login(self.user)
        url = reverse('post_new')
        http_response = self.client.post(url, self.invalid_form_post)
        self.assertEqual(http_response.status_code, 200)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')
        self.assertContains(
            http_response, 'This field is required.', html=True,
        )

    def test_post_edit_get_authorized(self):
        """Ensure authorized users have access to edit the post."""
        self.client.force_login(self.user)
        post = self.current_post
        url = reverse('post_edit', kwargs={'pk': post.pk})
        http_response = self.client.get(url)
        self.assertEqual(http_response.status_code, 200)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')

    def test_post_edit_get_unauthorized(self):
        """Ensure unauthorized users are redirected when edit a post."""
        self.client.logout()
        url = reverse('post_edit', kwargs={'pk': self.current_post.pk})
        http_response = self.client.get(url)
        self.assertRedirects(http_response, f'/accounts/login/?next={url}')

    def test_post_edit_valid_form_authorized(self):
        """Check the correctness of updating the post after editing."""
        self.client.force_login(self.user)
        post = self.current_post
        url = reverse('post_edit', kwargs={'pk': post.pk})
        updated_form_data = self.valid_form_post.copy()
        updated_form_data['title'] = 'Updated Title'
        updated_form_data['text'] = 'Updated Text'
        initial_published_date = post.published_date
        http_response = self.client.post(url, updated_form_data, follow=True)
        self.assertEqual(http_response.status_code, 200)
        self.assertTemplateUsed(http_response, 'blog/post_detail.html')
        self.assertRedirects(
            http_response, reverse(
                'post_detail', kwargs={'pk': post.pk},
            ),
        )
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Title')
        self.assertEqual(post.text, 'Updated Text')
        self.assertEqual(post.author, self.user)
        self.assertNotEqual(post.published_date, initial_published_date)

    def test_post_edit_invalid_form_authorized(self):
        """Test handling of invalid form submission when editing a post."""
        self.client.force_login(self.user)
        url = reverse('post_edit', kwargs={'pk': self.current_post.pk})
        http_response = self.client.post(url, self.invalid_form_post)
        self.assertEqual(http_response.status_code, 200)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')
        self.assertContains(
            http_response, 'This field is required.', html=True,
        )
