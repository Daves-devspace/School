from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.urls import reverse

from .models import Teacher, Role, Department, TeacherRole
from django.db import transaction

from ..management.models import Profile


@receiver(post_save, sender=Teacher)
def create_or_update_user(sender, instance, created, **kwargs):
    with transaction.atomic():
        if created:
            # Create the user without a password initially
            user = User.objects.create(
                username=instance.staff_number,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email,
            )
            user.set_unusable_password()  # User can't log in yet, no password set
            user.save()

            # Send password reset email
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.SITE_URL}{reverse('password_reset_confirm', kwargs={'uidb64': user.pk, 'token': token})}"
            send_mail(
                'Password Reset Request',
                f'Click here to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
            )

            # Link the user to the teacher instance
            instance.user = user
            instance.save()

        else:
            if not instance.user:
                user = User.objects.create(
                    username=instance.staff_number,
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    email=instance.email,
                )
                user.set_unusable_password()  # Or a default password, if needed
                user.save()
                instance.user = user
            else:
                instance.user.username = instance.staff_number
                instance.user.first_name = instance.first_name
                instance.user.last_name = instance.last_name
                instance.user.email = instance.email
                instance.user.save()

        instance.save()  # Save teacher instance if any changes occurred

@receiver(post_save, sender=Teacher)
def ensure_teacher_profile(sender, instance, created, **kwargs):
    """ Ensure the user is linked and has a teacher role in Profile """
    if instance.user:
        profile, _ = Profile.objects.get_or_create(user=instance.user)
        if profile.role != 'Teacher':  # Prevent unnecessary updates
            profile.role = 'Teacher'
            profile.save()



@receiver(post_save, sender=Teacher)
def auto_assign_roles(sender, instance, created, **kwargs):
    if created:
        # Example: Assign new teacher to all departments with default roles
        default_roles = Role.objects.filter(name__in=['Dean', 'Sports'])
        for department in Department.objects.all():
            for role in default_roles:
                TeacherRole.objects.get_or_create(teacher=instance, department=department, role=role)

