from django import forms
from .models import Subject, TeacherSubject, Term, SubjectMark
from ..students.models import Student, Class, Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title','author','year','subject','isbn']
        widgets = {
            'title':forms.TextInput(attrs={'class':'form-control','placeholder':'Book Title'}),
            'author':forms.TextInput(attrs={'class':'form-control'}),
            'year':forms.DateInput(attrs={'type':'date'}),
            'subject':forms.TextInput(attrs={'class':'form-control'}),
            'isbn':forms.TextInput(attrs={'class':'form-control'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'grade']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Name'}),
            'grade_assigned': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }




class AddResultForm(forms.ModelForm):
    class_name = forms.ModelChoiceField(queryset=Class.objects.all(), required=True, label="Class")
    student = forms.ModelChoiceField(queryset=Student.objects.none(), required=True, label="Student")
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=True, label="Subject")
    marks = forms.IntegerField(min_value=0, required=True, label="Marks")

    class Meta:
        model = SubjectMark
        fields = ['class_name', 'student', 'subject', 'marks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'class_name' in self.initial:
            class_id = self.initial['class_name']
            self.fields['student'].queryset = Student.objects.filter(class_name_id=class_id)
        else:
            self.fields['student'].queryset = Student.objects.none()







