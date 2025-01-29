from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber
from phonenumbers import parse, is_valid_number, NumberParseException

from .models import Teacher, TeacherAssignment
from ..management.models import Profile



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
        required=False  # Password is optional for updates
    )
    phone = PhoneNumberField(required=False)  # Optional phone number
    address = forms.CharField(widget=forms.Textarea, required=False)  # Optional address

    class Meta:
        model = Teacher
        fields = [
            'full_name', 'id_No', 'staff_number', 'phone', 'gender',
            'qualification', 'experience', 'joining_date',
            'subjects', 'country', 'address'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'staff_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualification'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Experience (in years)'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
        }

    def __init__(self, *args, **kwargs):
        # Handle instance for updates
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Populate email for updates
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            # Hide password field during updates
            self.fields['password'].widget = forms.HiddenInput()

        # Auto-generate staff number for new teachers
        if not self.instance or not self.instance.pk:
            self.fields['staff_number'].initial = Teacher.generate_staff_number()

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Ensure email is unique for the User model
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk if self.instance and self.instance.user else None).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', None)

        # If phone is provided, check if it is valid
        if phone:
            # Ensure phone is a string, not a PhoneNumber object
            if isinstance(phone, str):
                raw_phone_number = phone
            else:
                raw_phone_number = str(phone)  # Convert PhoneNumber object to string

            # Check if it starts with '07' for Kenyan numbers and format correctly
            if raw_phone_number.startswith('07'):
                phone = '+254' + raw_phone_number[1:]  # Convert '07' to '+2547'
            elif not raw_phone_number.startswith('+254'):
                raise forms.ValidationError("Enter a valid Kenyan number starting with +254 or 07.")

            # Validate the phone number using phonenumbers library
            try:
                parsed_number = parse(phone, 'KE')
                if not is_valid_number(parsed_number):
                    raise ValueError("Invalid phone number format.")
            except (NumberParseException, ValueError) as e:
                raise forms.ValidationError(f"Invalid phone number: {str(e)}")

            self.cleaned_data['phone'] = phone  # Update the phone number after formatting

        return phone

    def save(self, commit=True):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        # Update or create the associated User
        if self.instance and self.instance.user:
            user = self.instance.user
            user.email = email
            user.username = self.instance.staff_number  # Use staff_number as username
            if password:
                user.set_password(password)
            if commit:
                user.save()
        else:
            # Create new user for new teacher
            user = User.objects.create_user(username=self.instance.staff_number, email=email, password=password)

        # Save Teacher instance
        teacher = super().save(commit=False)
        teacher.user = user

        if commit:
            teacher.save()
            self.save_m2m()

        return teacher







class TeacherAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherAssignment
        fields = ['teacher','subject','grade_section']
        widgets = {
            'teacher' : forms.Select(attrs={'class':'form-control'}),
            'subject' : forms.Select(attrs={'class':'form-control'}),
            'grade_section' : forms.Select(attrs={'class':'form-control'}),

        }
    #validation
    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        subject = cleaned_data.get('subject')
        grade_section = cleaned_data.get('grade_section')

        if TeacherAssignment.objects.filter(teacher=teacher, subject=subject, grade_section=grade_section).exists():
            raise forms.ValidationError('This teacher is already assigned to this subject and grade section.')

        return cleaned_data



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