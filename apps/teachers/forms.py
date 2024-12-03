from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Teacher
from ..management.models import Performance


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['user_name','full_name','phone_no','subjects','joining_date']
        widgets = {'joining_date':forms.DateInput(attrs={'class':'datepicker','type':'date'}) }

class PerformanceForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = ['student', 'marks', 'total_marks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }