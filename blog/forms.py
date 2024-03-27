"""Form class for the Blog application."""

from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    """Form for the creation of new posts in the Blog application."""

    class Meta:
        """Metadata for the post form."""

        model = Post
        fields = ('title', 'text')
