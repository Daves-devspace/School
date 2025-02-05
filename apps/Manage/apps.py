from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import connection




class ManageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # For Django 3.2+
    name = 'apps.Manage'  # Use lowercase name for apps

    def ready(self):
        # Connect the post_migrate signal to the after_migrate function
        post_migrate.connect(self.after_migrate, sender=self)

    def after_migrate(self, sender, **kwargs):
        """
        Perform database operations after migrations are completed.
        """
        try:
            with connection.cursor() as cursor:
                # Example of custom logic: replace with your actual operations
                cursor.execute("SELECT 1;")  # Placeholder query
        except Exception as e:
            # Log or handle exceptions gracefully
            print(f"Error during post_migrate: {e}")
