"""The admin configuration for the Blog application."""


from django.contrib import admin

from .models import Post

admin.site.register(Post)
