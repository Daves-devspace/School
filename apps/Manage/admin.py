from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm
from .models import SmsProviderToken

# Get the custom user model dynamically
User = get_user_model()

# Register the SmsProviderToken model in the admin
@admin.register(SmsProviderToken)
class SmsProviderTokenAdmin(admin.ModelAdmin):
    list_display = ('sender_id', 'api_token')

# Custom User Admin to use the custom user creation form
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm  # Use the custom form for user creation
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('date_joined',)


# # Register the Custom User Admin with the User model
# admin.site.register(User, CustomUserAdmin)
