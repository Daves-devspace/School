from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['user_name','full_name','phone_no','subjects','joining_date']
        widgets = {'joining_date':forms.DateInput(attrs={'class':'datepicker','type':'date'}) }