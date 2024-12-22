from django import forms
from .models import Subject, TeacherSubject, Term
from ..students.models import Student


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'grade']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Name'}),
            'grade_assigned': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }




class AddResultForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        label="Student",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label="Teacher and Subject",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        label="Term",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    score = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Score",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
