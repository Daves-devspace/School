from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Student



GENDER_CHOICES = {"Male":"Male","Female":"Female"}
RELIGION_CHOICES = {"Christian":"Christian","Muslim":"Muslim"}
class StudentForm(forms.ModelForm):
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)  # form.select
    religion = forms.ChoiceField(choices=RELIGION_CHOICES, widget=forms.Select)

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth',
            'grade', 'religion', 'joining_date',
            'admission_number', 'student_image',
            'parent_name', 'parent_mobile',
            'guardian_name','student_relationship', 'guardian_mobile',
            'address'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
        }
