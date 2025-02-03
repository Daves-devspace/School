from django import forms

from apps.website.models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['guardian_name', 'email', 'phone', 'child_name', 'date', 'time', 'message']
        widgets = {
            'guardian_name': forms.TextInput(attrs={'class': 'form-control border-0', 'placeholder': 'Guardian Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control border-0', 'placeholder': 'Guardian Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control border-0', 'placeholder': 'Phone'}),
            'child_name': forms.TextInput(attrs={'class': 'form-control border-0', 'placeholder': 'Child Name'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control border-0'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control border-0'}),
            'message': forms.Textarea(attrs={'class': 'form-control border-0', 'placeholder': 'Leave a message here', 'style': 'height: 100px'}),
        }
