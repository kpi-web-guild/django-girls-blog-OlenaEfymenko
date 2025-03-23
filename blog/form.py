"""Form class."""

from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    """Main form for Post."""

    class Meta:
        """Metadata for post form."""
        model = Post
        fields = ('title', 'text')