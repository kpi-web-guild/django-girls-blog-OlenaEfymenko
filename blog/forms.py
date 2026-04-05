"""The forms for the Blog application."""

from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    """Form for editing posts in the Blog application."""

    class Meta:
        """Metadata for the post form."""

        model = Post
        fields = ('title', 'text')
