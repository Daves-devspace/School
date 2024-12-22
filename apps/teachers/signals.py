from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Teacher, Role, Department, TeacherRole

@receiver(post_save, sender=Teacher)
def auto_assign_roles(sender, instance, created, **kwargs):
    if created:
        # Example: Assign new teacher to all departments with default roles
        default_roles = Role.objects.filter(name__in=['Dean', 'Sports'])
        for department in Department.objects.all():
            for role in default_roles:
                TeacherRole.objects.get_or_create(teacher=instance, department=department, role=role)
