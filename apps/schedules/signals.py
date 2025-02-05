from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.management.models import Notification
from apps.schedules.models import TimetableSlot

#
# @receiver(post_save, sender=TimetableSlot)
# def notify_reschedule(sender, instance, created, **kwargs):
#     if instance.is_rescheduled:
#         Notification.objects.create(
#             recipient=instance.teacher_assignment.grade_section.class_teacher.user,
#             message=f"Class rescheduled: {instance.teacher_assignment.subject.name}",
#             content_object=instance
#         )

# signals.py
@receiver(post_save, sender=TimetableSlot)
def create_reschedule_notification(sender, instance, created, **kwargs):
    if created and instance.is_rescheduled:
        message = f"Your {instance.teacher_assignment.subject.name} class has been rescheduled"
        Notification.objects.create(
            user=instance.teacher_assignment.teacher.user,
            message=message,
            link=f"/schedule/{instance.id}/"
        )