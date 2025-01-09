from django import forms
from django.contrib.auth.models import User
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber

from .models import Teacher




class TeacherForm(forms.ModelForm):
    # Additional fields for user authentication
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter email'
    }))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        required=False  # Password is not required for updates
    )

    class Meta:
        model = Teacher
        fields = [
            'full_name', 'teacher_id', 'phone_no', 'gender',
            'qualification', 'experience', 'joining_date',
            'subjects', 'country', 'address'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'teacher_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teacher ID'
            }),
            'phone_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Qualification'
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Experience (in years)'
            }),
            'joining_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'subjects': forms.SelectMultiple(attrs={
                'class': 'form-control',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Address',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        # Check if the form is for updating an existing instance
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user:  # If editing an existing teacher
            self.fields['email'].initial = self.instance.user.email  # Prepopulate email
            self.fields['password'].widget = forms.HiddenInput()  # Hide password field during updates

    def save(self, commit=True):
        # Extract email from cleaned data
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if self.instance and self.instance.user:  # Updating existing teacher
            user = self.instance.user
            user.email = email  # Update email
            user.username = email  # Update username (if needed)
            if commit:
                user.save()
        else:  # Creating a new teacher
            user = User.objects.create_user(username=email, email=email, password=password)

        # Save the Teacher instance
        teacher = super().save(commit=False)
        teacher.user = user
        if commit:
            teacher.save()
            self.save_m2m()  # Save many-to-many relationships (e.g., subjects)
        return teacher

#
# class TeacherForm(forms.ModelForm):
#     phone_no = forms.CharField(
#         widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}),
#     )
#
#     class Meta:
#         model = Teacher
#         fields = [
#              'full_name','teacher_id', 'phone_no','gender',
#             'qualification', 'experience', 'joining_date',
#             'subjects','country', 'address'
#         ]
#         widgets = {
#             'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
#             'joining_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#             'subjects': forms.SelectMultiple(),
#         }
#
#         def clean_phone_no(self):
#             phone_no = self.cleaned_data['phone_no']
#             # Validate format for Kenyan numbers
#             if phone_no.startswith('07'):
#                 phone_no = '+254' + phone_no[1:]  # Convert '07' to '+2547'
#             elif not phone_no.startswith('+254'):
#                 raise forms.ValidationError("Enter a valid Kenyan number starting with +254 or 07.")
#
#             # Validate using phonenumber_field
#             validate_international_phonenumber(phone_no)
#             return phone_no



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