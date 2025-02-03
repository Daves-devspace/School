from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.shortcuts import render

from apps.website.forms import AppointmentForm


# Create your views here.
def contact_us(request):
    return render(request, 'Home/website/contact.html')


def about_us(request):
    return render(request,'Home/website/about.html')

def appointment_view(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()

            # Trigger real-time update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "appointments",
                {"type": "send_appointment_count"}
            )

            return JsonResponse({"message": "Appointment booked successfully!"}, status=201)
    else:
        form = AppointmentForm()
    return render(request, "Home/website/index.html", {"form": form})