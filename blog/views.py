"""The views for the Blog application."""

from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Post


def post_list(request):
    """Display the posts ordered by published date."""
    posts = (
        Post.objects
        .filter(published_date__lte=timezone.now())
        .order_by('published_date')
    )
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, pk):
    """Display a blog post based on the post's primary key."""
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})
