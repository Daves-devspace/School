from django import forms
from django.db.models.fields import CharField
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber

from .models import Student, Parent, StudentParent, Class

# Define Choices
GENDER_CHOICES = [("Male", "Male"), ("Female", "Female")]
RELIGION_CHOICES = [("Christian", "Christian"), ("Muslim", "Muslim"), ("Other", "Other")]
RELATIONSHIP_CHOICES = [("Father", "Father"), ("Mother", "Mother"), ("Guardian", "Guardian"), ("Other", "Other")]


class StudentForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(),
    )
    religion = forms.ChoiceField(
        choices=RELIGION_CHOICES,
        widget=forms.Select(),
    )
    parent_relationship = forms.ChoiceField(
        choices=RELATIONSHIP_CHOICES,
        widget=forms.Select(),
    )

    parent_first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Parent First Name'}),
    )
    parent_last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Parent Last Name'}),
    )
    parent_mobile = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Parent Mobile'}),
    )
    parent_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Parent Email'}),
    )
    parent_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Parent Address'}),
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth',
            'grade', 'religion', 'joining_date',
            'admission_number', 'student_image',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Student First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Student Last Name'}),
            'admission_number': forms.TextInput(attrs={'placeholder': 'Admission Number'}),
            'student_image': forms.FileInput(),
        }

    def clean_parent_mobile(self):
        mobile = self.cleaned_data['parent_mobile']
        # Validate format for Kenyan numbers
        if mobile.startswith('07'):
            mobile = '+254' + mobile[1:]  # Convert '07' to '+2547'
        elif not mobile.startswith('+254'):
            raise forms.ValidationError("Enter a valid Kenyan number starting with +254 or 07.")

        # Validate using phonenumber_field
        validate_international_phonenumber(mobile)
        return mobile

    def save(self, commit=True):
        # Save student information first
        student = super().save(commit=False)
        if commit:
            student.save()

        # Save or update parent information
        parent_data = {
            "first_name": self.cleaned_data["parent_first_name"],
            "last_name": self.cleaned_data["parent_last_name"],
            "mobile": self.cleaned_data["parent_mobile"],
            "email": self.cleaned_data.get("parent_email"),
            "address": self.cleaned_data.get("parent_address"),
        }
        parent, created = Parent.objects.get_or_create(
            first_name=parent_data["first_name"],
            last_name=parent_data["last_name"],
            mobile=parent_data["mobile"],
            defaults=parent_data,
        )

        # Link parent to the student
        relationship = self.cleaned_data["parent_relationship"]
        StudentParent.objects.get_or_create(student=student, parent=parent, relationship=relationship)

        return student


class PromoteStudentsForm(forms.Form):
    confirm = forms.BooleanField(
        label="Confirm Promotion",
        required=True,
        help_text="Tick this box to confirm the promotion of students."
    )


class SendSMSForm(forms.Form):
    message = forms.CharField(
        required=True,
        label="Message",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Type your message here..."
        })
    )




class SendClassForm(forms.Form):
    message = forms.CharField(
        required=True,
        label="Message",
        widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Enter message"})
    )
    class_choice = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=True,
        label="Class",
        widget=forms.Select(attrs={"class": "form-control"})
    )