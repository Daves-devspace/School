from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Teacher, Role, Department, TeacherRole




@receiver(post_save, sender=Teacher)
def create_or_update_user(sender, instance, created, **kwargs):
    """
    Ensure that the User model is created or updated with the teacher's staff_number as the username.
    """
    if created:
        # Create the associated User
        user = User.objects.create(
            username=instance.staff_number,  # Set staff_number as the login username
            first_name=instance.username,   # Use teacher's display name for User's first_name
            email=instance.email,
        )
        user.set_unusable_password()  # Optionally disable login until explicitly enabled
        user.save()
        instance.user = user
        instance.save()
    else:
        # Update the associated User if the teacher is updated
        if instance.user:
            instance.user.username = instance.staff_number
            instance.user.first_name = instance.username
            instance.user.email = instance.email
            instance.user.save()





@receiver(post_save, sender=Teacher)
def auto_assign_roles(sender, instance, created, **kwargs):
    if created:
        # Example: Assign new teacher to all departments with default roles
        default_roles = Role.objects.filter(name__in=['Dean', 'Sports'])
        for department in Department.objects.all():
            for role in default_roles:
                TeacherRole.objects.get_or_create(teacher=instance, department=department, role=role)

