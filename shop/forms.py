from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import Comment
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('author', 'text',)


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email