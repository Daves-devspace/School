from django import forms
from django.db.models.fields import CharField
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber

from .models import Student, Parent, StudentParent, Grade, StudentDocument, GradeSection
from ..management.models import ExamType, Term

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
            'admission_number': forms.TextInput(attrs={'readonly': 'readonly'}),
            'student_image': forms.FileInput(),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # If adding a new student (not editing)
            self.initial['admission_number'] = Student.generate_admission_number()

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

    def _get_or_create_parent(self, parent_data):
        # Update or create the parent record
        parent, created = Parent.objects.get_or_create(
            first_name=parent_data["first_name"],
            last_name=parent_data["last_name"],
            mobile=parent_data["mobile"],
            defaults=parent_data,
        )
        if not created:
            # Update the existing parent with new data
            for key, value in parent_data.items():
                if value:  # Only update non-empty fields
                    setattr(parent, key, value)
            parent.save()
        return parent

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()

        # Prepare parent data
        parent_data = {
            "first_name": self.cleaned_data["parent_first_name"],
            "last_name": self.cleaned_data["parent_last_name"],
            "mobile": self.cleaned_data["parent_mobile"],
            "email": self.cleaned_data.get("parent_email"),
            "address": self.cleaned_data.get("parent_address"),
        }

        # Get or create the parent
        parent = self._get_or_create_parent(parent_data)

        # Link parent to the student
        relationship = self.cleaned_data["parent_relationship"]
        StudentParent.objects.get_or_create(student=student, parent=parent, relationship=relationship)

        return student


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ['document']
        widgets ={
            'documents': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',  # Bootstrap class for file inputs
                'accept': '.pdf,.doc,.docx,.jpg,.png',  # Restrict file types
            }),
        }



class PromoteStudentsForm(forms.Form):
    confirm = forms.BooleanField(
        label="Confirm Promotion",
        required=True,
        help_text="Tick this box to confirm the promotion of students."
    )


class SendSMSForms(forms.Form):
    message = forms.CharField(
        required=True,
        label="Message",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Type your message here..."
        })
    )


class SendSMSForm(forms.Form):
    term = forms.ModelChoiceField(queryset=Term.objects.all(), label="Select Term", required=True)
    exam_type = forms.ModelChoiceField(queryset=ExamType.objects.all(), label="Select Exam Type", required=True)
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your message template here.'}),
        label="Message Template", required=True)


class ResultsSMSForm(forms.Form):
    term = forms.ModelChoiceField(queryset=Term.objects.all(), required=True, label="Term")
    exam_type = forms.ModelChoiceField(queryset=ExamType.objects.all(), required=True, label="Exam Type")
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=True, label="Message")

    class Meta:
        fields = ['term', 'exam_type', 'message']


class SendClassForm(forms.Form):
    message = forms.CharField(
        required=True,
        label="Message",
        widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Enter message"})
    )
    class_choice = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        required=True,
        label="Class",
        widget=forms.Select(attrs={"class": "form-control"})
    )




class StudentSearchForm(forms.Form):
    grade = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Grade Name"})
    )
    section = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Section Name"})
    )