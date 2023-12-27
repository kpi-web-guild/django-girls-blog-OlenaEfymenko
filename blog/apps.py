"""The Blog application configuration."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Blog app configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
