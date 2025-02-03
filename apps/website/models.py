from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Appointment(models.Model):
    guardian_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    child_name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Add fields to track reply status
    reply_status = models.CharField(max_length=50, choices=[('success', 'Success'), ('failed', 'Failed')],
                                    default='failed')
    reply_message = models.TextField(null=True, blank=True)  # Stores the reply message
    reply_failure_reason = models.TextField(null=True, blank=True)  # Stores the failure reason (if any)

    def __str__(self):
        return f"Appointment with {self.guardian_name} on {self.date} at {self.time}"


class AppointmentReply(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="replies")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)