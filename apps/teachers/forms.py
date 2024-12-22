from django import forms
from django.contrib.auth.models import User
from phonenumber_field.formfields import PhoneNumberField


from ..management.models import  Subject, Teacher




class TeacherForm(forms.ModelForm):

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