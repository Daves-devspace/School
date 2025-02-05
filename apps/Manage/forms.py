from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .validators import custom_username_validator
from .models import SmsProviderToken
import string
import random

# Get user model dynamically (whether custom or default)
User = get_user_model()

# Custom SignUp form
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


# SMS Provider Token Form
class SmsProviderTokenForm(forms.ModelForm):
    class Meta:
        model = SmsProviderToken
        fields = ['api_token', 'sender_id']


# User Creation Form
class UserCreateForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, help_text="Assign a role to the user")

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_staff', 'is_superuser']

    def generate_random_password(self, length=12):
        """Generate a secure random password"""
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))

    def save(self, commit=True):
        user = super().save(commit=False)
        random_password = self.generate_random_password()
        user.set_password(random_password)  # Hash and save the password
        if commit:
            user.save()
            user.groups.add(self.cleaned_data["role"])  # Assign role
            self.send_welcome_email(user, random_password)  # Send email with login details
        return user

    def send_welcome_email(self, user, password):
        """Send email notification with login credentials"""
        from django.core.mail import send_mail
        subject = "Welcome to the System - Your Login Credentials"
        message = f"""
        Hi {user.username},

        Your account has been created successfully. Below are your login details:

        Username: {user.username}
        Password: {password}

        Please log in and change your password immediately for security reasons.

        Login URL: https://merryland.com/login/

        Best regards,
        Director
        """
        send_mail(subject, message, 'admin@yourwebsite.com', [user.email])




class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        validators=[custom_username_validator],  # Apply custom validator
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # Include password1 and password2
