"""The views for the Blog application."""

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.shortcuts import redirect

from .models import Post
from .forms import PostForm


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


def post_new(request):
    """Create a new post."""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm
    return render(request, 'blog/post_edit.html', {'form': form})
    
