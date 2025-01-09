from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        # Connect the post_migrate signal to the after_migrate function
        post_migrate.connect(self.after_migrate, sender=self)

    def after_migrate(self, sender, **kwargs):
        """
        Perform database operations after migrations are completed.
        """
        # Avoid direct queries here unless necessary
        # Instead, ensure operations are lightweight
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Example: Custom logic after migrations
                # Replace 'your_query_here' with actual SQL if necessary
                cursor.execute("SELECT 1;")  # Placeholder query
        except Exception as e:
            # Log or handle exceptions
            print(f"Error during post_migrate: {e}")
