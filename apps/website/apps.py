from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import connection

class WebsiteConfig(AppConfig):
    name = 'apps.website'  # Ensure this reflects your actual app name

    def ready(self):
        # Connect the post_migrate signal to the after_migrate method
        post_migrate.connect(self.after_migrate, sender=self)

    def after_migrate(self, sender, **kwargs):
        """
        Perform database operations after migrations are completed.
        """
        try:
            with connection.cursor() as cursor:
                # Example: Custom query logic (replace with actual logic)
                cursor.execute("SELECT 1;")  # Placeholder query
        except Exception as e:
            # Handle any exceptions during the database operation
            print(f"Error during post_migrate signal: {e}")
