from django import forms
from phonenumber_field.formfields import PhoneNumberField
from .models import Student, Parent, StudentParent

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
    parent_mobile = PhoneNumberField(
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
            'Class', 'religion', 'joining_date',
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
























# from django import forms
# from phonenumber_field.formfields import PhoneNumberField
#
# from .models import Student
#
#
#
# GENDER_CHOICES = {"Male":"Male","Female":"Female"}
# RELIGION_CHOICES = {"Christian":"Christian","Muslim":"Muslim"}
# RELATIONSHIP_CHOICES = {"Father":"Father", "Mother":"Mother", "Guardian":"Guardian", "Other":"Other"}
# class StudentForm(forms.ModelForm):
#     gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)  # form.select
#     religion = forms.ChoiceField(choices=RELIGION_CHOICES, widget=forms.Select)
#     student_relationship = forms.ChoiceField(choices=RELATIONSHIP_CHOICES,widget=forms.Select)
#
#     class Meta:
#         model = Student
#         fields = [
#             'first_name', 'last_name', 'gender', 'date_of_birth',
#             'class', 'religion', 'joining_date',
#             'admission_number', 'student_image',
#             'parent_name', 'parent_mobile',
#             'guardian_name','student_relationship', 'guardian_mobile',
#             'address'
#         ]
#         widgets = {
#             'date_of_birth': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
#             'joining_date': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
#         }
