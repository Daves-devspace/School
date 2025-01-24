from django import forms
from django.contrib.auth.models import User
from django.utils.timezone import now
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber

from .models import Teacher
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
        required=False  # Password is not required for updates
    )
    phone_no = PhoneNumberField(required=False)  # Optional phone number field for profile
    address = forms.CharField(widget=forms.Textarea, required=False)  # Optional address field for profile

    class Meta:
        model = Teacher
        fields = [
            'full_name', 'id_No', 'staff_number', 'phone_no', 'gender',
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
            'staff_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',  # Make the staff number read-only
            }),
        }

    def __init__(self, *args, **kwargs):
        # Check if the form is for updating an existing instance
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Generate staff number automatically if not set (new teacher)
        if not self.instance.pk:  # Only generate for new teachers
            self.fields['staff_number'].initial = Teacher.generate_staff_number()

        if self.instance and self.instance.user:  # If editing an existing teacher
            self.fields['email'].initial = self.instance.user.email  # Prepopulate email
            self.fields['password'].widget = forms.HiddenInput()  # Hide password field during updates

    def clean_phone_no(self):
        mobile = self.cleaned_data['phone_no']

        # Ensure the mobile number is a string
        mobile_str = str(mobile)

        # Validate format for Kenyan numbers
        if mobile_str.startswith('07'):
            mobile_str = '+254' + mobile_str[1:]  # Convert '07' to '+2547'
        elif not mobile_str.startswith('+254'):
            raise forms.ValidationError("Enter a valid Kenyan number starting with +254 or 07.")

        # Validate using phonenumber_field
        validate_international_phonenumber(mobile_str)

        # Convert back to a PhoneNumber object and return
        return PhoneNumber.from_string(mobile_str)

    def save(self, commit=True):
        # Extract email and password from cleaned data
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if self.instance and self.instance.user:  # Updating existing teacher
            user = self.instance.user
            user.email = email  # Update email
            user.username = email  # Update username (if needed)
            if password:  # Update password if provided
                user.set_password(password)
            if commit:
                user.save()
        else:  # Creating a new teacher
            user = User.objects.create_user(username=email, email=email, password=password)

        # Save the Teacher instance, generating staff_number automatically if not set
        teacher = super().save(commit=False)
        if not teacher.staff_number:  # Only generate staff_number for new teachers
            teacher.staff_number = Teacher.generate_staff_number()  # Assuming you have this method in your model
        teacher.user = user

        # Save the Teacher instance
        if commit:
            teacher.save()
            self.save_m2m()  # Save many-to-many relationships (e.g., subjects)

            # Create Profile instance
            profile = Profile.objects.create(
                user=user,  # Link the profile to the user
                role='Teacher',  # Role is set to 'Teacher' by default
                phone_number=self.cleaned_data.get('phone_no', ''),  # Phone number
                address=self.cleaned_data.get('address', ''),  # Address
                created_at=now(),  # Set the profile creation time
            )

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