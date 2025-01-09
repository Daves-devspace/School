from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomSignupForm(UserCreationForm):
    ROLE_CHOICES = [
        ('Teacher', 'Teacher'),
        ('Head Teacher', 'Head Teacher'),
        ('Director', 'Director'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']