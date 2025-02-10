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


def generate_random_password():
    """Generate a secure random password."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


@receiver(post_save, sender=Teacher)
def create_or_update_user(sender, instance, created, **kwargs):
    """
    When a Teacher is created, ensure a linked User is created with a random password.
    """
    with transaction.atomic():
        if created:
            random_password = generate_random_password()

            user = User.objects.create(
                username=instance.staff_number,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email,
            )
            user.set_password(random_password)  # Set random password
            user.save()

            # Generate password reset link
            token = default_token_generator.make_token(user)
            reset_link = f"{settings.SITE_URL}{reverse('password_reset_confirm', kwargs={'uidb64': user.pk, 'token': token})}"

            # Send email with password & reset link
            email_subject = "Your Account Credentials"
            email_body = (
                f"Hello {instance.first_name},\n\n"
                f"Your account has been created.\n"
                f"Username: {user.username}\n"
                f"Temporary Password: {random_password}\n\n"
                f"You can reset your password using this link: {reset_link}\n\n"
                f"Please change your password after logging in.\n\n"
                f"Best regards,\nMerryland"
            )
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
            )

            # Link the user to the teacher instance
            instance.user = user
            instance.save()

        else:
            if not instance.user:
                random_password = generate_random_password()

                user = User.objects.create(
                    username=instance.staff_number,
                    first_name=instance.first_name,
                    last_name=instance.last_name,
                    email=instance.email,
                )
                user.set_password(random_password)
                user.save()
                instance.user = user

            else:
                instance.user.username = instance.staff_number
                instance.user.first_name = instance.first_name
                instance.user.last_name = instance.last_name
                instance.user.email = instance.email
                instance.user.save()

        instance.save()  # Save teacher instance after user updates


@receiver(post_save, sender=Teacher)
def ensure_teacher_profile(sender, instance, created, **kwargs):
    """
    Ensure the user linked to a Teacher has the correct role in Profile.
    """
    if instance.user:
        Profile.objects.update_or_create(
            user=instance.user,
            defaults={'role': 'Teacher'}  # Ensure the role is always 'Teacher'
        )




@receiver(post_save, sender=Teacher)
def auto_assign_roles(sender, instance, created, **kwargs):
    if created:
        # Example: Assign new teacher to all departments with default roles
        default_roles = Role.objects.filter(name__in=['Dean', 'Sports'])
        for department in Department.objects.all():
            for role in default_roles:
                TeacherRole.objects.get_or_create(teacher=instance, department=department, role=role)

