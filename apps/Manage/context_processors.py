from apps.schedules.models import Notification
from apps.website.models import Appointment



def notifications_and_appointments(request):
    if not request.user.is_authenticated:
        return {}

    # Fetch unread notifications
    unread_notifications = Notification.objects.filter(read=False).count()
    notifications = Notification.objects.order_by('-created_at')[:10]

    # Fetch unread appointments
    unread_appointments = Appointment.objects.filter(reply_status='pending').count()
    appointments = Appointment.objects.order_by('-created_at')[:5]

    return {
        'unread_notifications': unread_notifications,
        'notifications': notifications,
        'unread_appointments': unread_appointments,
        'appointments': appointments,
    }

