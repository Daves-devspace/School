from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import connection




class TeacherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.teachers'

    def ready(self):
        import apps.teachers.signals  # Import the signals to register them





class TeachersConfig(AppConfig):
    name = 'apps.teachers'

    def ready(self):
        # Connect the post_migrate signal to the after_migrate method
        post_migrate.connect(self.after_migrate, sender=self)

    def after_migrate(self, sender, **kwargs):
        """
        Perform database operations after migrations are completed.
        """
        try:
            with connection.cursor() as cursor:
                # Example: Execute a custom query (replace with your logic)
                cursor.execute("SELECT 1;")  # Placeholder query
        except Exception as e:
            # Log or handle exceptions gracefully
            print(f"Error during post_migrate signal: {e}")

