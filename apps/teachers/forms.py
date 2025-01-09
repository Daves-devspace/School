from django import forms
from django.contrib.auth.models import User
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber

from ..management.models import  Subject, Teacher




class TeacherForm(forms.ModelForm):
    phone_no = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}),
    )

    class Meta:
        model = Teacher
        fields = [
             'full_name','teacher_id', 'phone_no','gender',
            'qualification', 'experience', 'joining_date',
            'subjects','country', 'address'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'subjects': forms.SelectMultiple(),
        }

        def clean_phone_no(self):
            phone_no = self.cleaned_data['phone_no']
            # Validate format for Kenyan numbers
            if phone_no.startswith('07'):
                phone_no = '+254' + phone_no[1:]  # Convert '07' to '+2547'
            elif not phone_no.startswith('+254'):
                raise forms.ValidationError("Enter a valid Kenyan number starting with +254 or 07.")

            # Validate using phonenumber_field
            validate_international_phonenumber(phone_no)
            return phone_no



    #
    # def save(self, commit=True):
    #     # Save the User instance first
    #     user = User.objects.create_user(
    #         username=self.cleaned_data['username'],
    #         password=self.cleaned_data['password'],
    #         email=self.cleaned_data['email']
    #     )
    #
    #     # Save the Teacher instance and link the user
    #     teacher = super().save(commit=False)
    #     teacher.user = user
    #     if commit:
    #         teacher.save()
    #         self.save_m2m()  # Save ManyToMany fields (e.g., subjects)
    #     return teacher

# class PerformanceForm(forms.ModelForm):
#     class Meta:
#         model = Performance
#         fields = ['student', 'marks', 'total_marks']
#         widgets = {
#             'student': forms.Select(attrs={'class': 'form-control'}),
#             'marks': forms.NumberInput(attrs={'class': 'form-control'}),
#             'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
#         }