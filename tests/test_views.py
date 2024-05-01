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
        cls.user = get_user_model().objects.create_user(
            username='test user',
            password='test password',
        )
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

    def login_user_helper(self):
        """ADD."""
        self.client.force_login(self.user)

    def unauthorized_user_helper(self, url):
        """ADD."""
        http_response = self.client.get(url)
        self.assertRedirects(
            http_response, f'/accounts/login/?next={url}',
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

    def test_post_new_get_method_authorized_user(self):
        """Check that an authorized user can access the new post page."""
        self.login_user_helper()
        http_response = self.client.get(reverse('post_new'))
        self.assertEqual(200, http_response.status_code)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')

    def test_post_new_get_method_unauthorized_user(self):
        """Check that an unauthorized user is redirected to the login page."""
        self.unauthorized_user_helper(reverse('post_new'))

    def test_post_new_post_method_authorized_user_valid_form(self):
        """Check if authorized user can create a new post with valid form."""
        self.login_user_helper()
        http_response = self.client.post(
            reverse('post_new'), self.valid_form_post, follow=True,
        )
        self.assertEqual(200, http_response.status_code)
        new_post = Post.objects.filter(
            title='Test Title', text='Test Text',
        ).first()
        self.assertIsNotNone(new_post)
        self.assertRedirects(
            http_response, reverse(
                'post_detail', kwargs={'pk': new_post.pk},
            ),
        )
        self.assertTemplateUsed(http_response, 'blog/post_detail.html')

    def test_post_new_post_method_authorized_user_invalid_form(self):
        """Check if post can't be created when submitting an invalid form."""
        self.login_user_helper()
        http_response = self.client.post(
            reverse('post_new'), self.invalid_form_post,
        )
        self.assertEqual(200, http_response.status_code)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')
        self.assertEqual(Post.objects.count(), 3)
        self.assertTrue(http_response.context['form'].errors)
        self.assertContains(
            http_response, 'This field is required.', html=True,
        )

    def test_post_edit_get_method_authorized_user(self):
        """Check that an authorized user can access the edit post page."""
        self.login_user_helper()
        post = Post.objects.create(
            author=self.user, title='Test Post', text='Test Text',
        )
        http_response = self.client.get(
            reverse('post_edit', kwargs={'pk': post.pk}),
        )
        self.assertEqual(200, http_response.status_code)
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')

    def test_post_edit_get_method_unauthorized_user(self):
        """Check that an unauthorized user is redirected to the login page."""
        self.unauthorized_user_helper(reverse('post_edit', kwargs={'pk': 1}))

    def test_post_edit_post_method_authorized_user_valid_form(self):
        """Check if authorized user can edit post with valid form."""
        self.login_user_helper()
        post = Post.objects.create(
            author=self.user, title='Initial Title', text='Initial Text',
        )
        updated_form_data = self.valid_form_post.copy()
        updated_form_data['title'] = 'Updated Title'
        updated_form_data['text'] = 'Updated Text'
        http_response = self.client.post(
            reverse(
                'post_edit', kwargs={'pk': post.pk},
            ),
            updated_form_data, follow=True,
        )
        self.assertEqual(200, http_response.status_code)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Title')
        self.assertEqual(post.text, 'Updated Text')
        self.assertRedirects(
            http_response, reverse(
                'post_detail', kwargs={'pk': post.pk},
            ),
        )
        self.assertTemplateUsed(http_response, 'blog/post_detail.html')

    def test_post_edit_post_method_authorized_user_invalid_form(self):
        """Check if post can't be edited when submitting an invalid form."""
        self.login_user_helper()
        post = Post.objects.create(
            author=self.user, title='Initial Title', text='Initial Text',
        )
        http_response = self.client.post(
            reverse(
                'post_edit', kwargs={
                 'pk': post.pk,
                },
            ), self.invalid_form_post,
        )
        self.assertEqual(200, http_response.status_code)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Initial Title')
        self.assertEqual(post.text, 'Initial Text')
        self.assertTemplateUsed(http_response, 'blog/post_edit.html')
        self.assertTrue(http_response.context['form'].errors)
        self.assertContains(
            http_response, 'This field is required.', html=True,
        )
