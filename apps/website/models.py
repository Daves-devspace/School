from django.conf import settings

from django.db import models



class Appointment(models.Model):
    class ReplyStatus(models.TextChoices):  # Ensure TextChoices is used properly
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    guardian_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    child_name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Reply Tracking
    reply_status = models.CharField(
        max_length=10,
        choices=ReplyStatus.choices,  # Ensure choices are correctly referenced
        default=ReplyStatus.PENDING
    )
    reply_message = models.TextField(null=True, blank=True)
    reply_failure_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Appointment with {self.guardian_name} on {self.date} at {self.time}"


class AppointmentReply(models.Model):
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="replies"
    )
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.appointment.guardian_name} by {self.teacher}"
