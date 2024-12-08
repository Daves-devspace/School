from django import forms
from phonenumber_field.formfields import PhoneNumberField


from ..management.models import  Subject, Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['user_name','full_name','phone_no','subjects','joining_date']
        widgets = {'joining_date':forms.DateInput(attrs={'class':'datepicker','type':'date'}),
                   'subjects': forms.SelectMultiple(attrs={'class': 'form-control'}), } # Dropdown for multiple selection

        # Customizing the subjects field to dynamically load available subjects
    def clean_subjects(self):
        subjects = self.cleaned_data.get('subjects')
        # Ensure you're passing the ids of the subjects, not the objects themselves
        if not subjects:
            raise forms.ValidationError("At least one subject is required.")
        return subjects

# class PerformanceForm(forms.ModelForm):
#     class Meta:
#         model = Performance
#         fields = ['student', 'marks', 'total_marks']
#         widgets = {
#             'student': forms.Select(attrs={'class': 'form-control'}),
#             'marks': forms.NumberInput(attrs={'class': 'form-control'}),
#             'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
#         }