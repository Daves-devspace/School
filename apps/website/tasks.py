# from celery import shared_task
# from django.core.mail import send_mail
# from datetime import datetime, timedelta
# from .models import Appointment
#
#
# @shared_task
# def send_appointment_reminders():
#     upcoming_appointments = Appointment.objects.filter(
#         date=datetime.today(),
#         time__gte=datetime.now().time(),
#         reply_status='failed'  # Only send reminders for appointments that haven't been replied to
#     )
#
#     for appointment in upcoming_appointments:
#         try:
#             send_mail(
#                 "Appointment Reminder",
#                 f"Dear {appointment.guardian_name},\n\n"
#                 f"This is a reminder for your appointment on {appointment.date} at {appointment.time}.\n\n"
#                 "Best Regards,\nYour Team",
#                 "admin@yourwebsite.com",
#                 [appointment.email],
#             )
#             appointment.reply_status = "success"
#             appointment.reply_message = "Reminder email sent successfully."
#         except Exception as e:
#             appointment.reply_status = "failed"
#             appointment.reply_failure_reason = str(e)
#
#         appointment.save()
#
#     return f"Processed {upcoming_appointments.count()} reminders."
