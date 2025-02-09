from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import connection
from django.core.exceptions import FieldDoesNotExist


class ManageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.Manage'  # Changed from 'apps.Manage' to match standard Django app naming

    def ready(self):
        # Deferred imports
        from django.contrib.auth.models import User
        from .validators import custom_username_validator
        # Connect signals
        post_migrate.connect(self.after_migrate, sender=self)

        # Import inside ready() to avoid circular imports
        try:
            from django.contrib.auth.models import User
            from .validators import custom_username_validator

            # Update username validation
            self.update_username_validation(User, custom_username_validator)

        except ImportError:
            # Handle cases where models aren't loaded yet
            pass

    def update_username_validation(self, User, validator):
        """Update username field validators"""
        try:
            username_field = User._meta.get_field('username')

            # Preserve non-RegexValidator validators
            preserved_validators = [
                v for v in username_field.validators
                if not hasattr(v, 'regex')
            ]

            # Set new validators
            username_field.validators = [validator] + preserved_validators

            # Update help text
            from django.utils.translation import gettext_lazy as _
            username_field.help_text = _(
                "Required. 150 characters or fewer. Letters, digits and @/./+/-/_// allowed."
            )

        except FieldDoesNotExist:
            print("Warning: User model username field not found")

    def after_migrate(self, sender, **kwargs):
        """Post-migration operations"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")  # Your actual migration logic
        except Exception as e:
            print(f"Error during post_migrate: {e}")