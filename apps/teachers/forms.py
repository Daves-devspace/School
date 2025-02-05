from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumbers import parse, is_valid_number, NumberParseException

from .models import Teacher, TeacherAssignment
from ..management.models import Profile



class TeacherForm(forms.ModelForm):
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
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )  # Handle as a normal CharField for better validation

    address = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 3,
        'placeholder': 'Address'
    }), required=False)

    class Meta:
        model = Teacher
        fields = [
            'first_name', 'last_name', 'id_No', 'staff_number', 'phone', 'gender',
            'qualification', 'experience', 'joining_date',
            'subjects', 'country', 'address'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'id_No': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Number'}),
            'staff_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualification'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Experience (in years)'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Populate email for updates
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['password'].widget = forms.HiddenInput()  # Hide password field in updates

        # Auto-generate staff number only for new teachers
        if not self.instance or not self.instance.pk:
            self.fields['staff_number'].initial = Teacher.generate_staff_number()

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")

        # Ensure email is unique
        if Teacher.objects.filter(user__email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("This email is already associated with another teacher.")

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            if phone.startswith('07'):
                phone = '+254' + phone[1:]  # Convert '07' to '+2547'
            elif not phone.startswith('+254'):
                raise forms.ValidationError("Enter a valid Kenyan number starting with +254 or 07.")

            try:
                parsed_number = parse(phone, 'KE')
                if not is_valid_number(parsed_number):
                    raise forms.ValidationError("Invalid phone number format.")
            except NumberParseException:
                raise forms.ValidationError("Invalid phone number format.")

            validate_international_phonenumber(phone)  # Additional validation

        return phone

    def save(self, commit=True):
        teacher = super().save(commit=False)
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if not teacher.staff_number:
            teacher.staff_number = Teacher.generate_staff_number()

        # Handle User instance
        if teacher.user:
            user = teacher.user
            user.email = email
            user.username = teacher.staff_number
            if password:
                user.set_password(password)
            if commit:
                user.save()
        else:
            user = User.objects.create_user(username=teacher.staff_number, email=email,
                                            password=password if password else None)
            teacher.user = user

        if commit:
            teacher.save()
            self.save_m2m()

        return teacher


class TeacherAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherAssignment
        fields = ['teacher', 'subject', 'grade_section']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'grade_section': forms.Select(attrs={'class': 'form-control'}),

        }

    # validation
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
